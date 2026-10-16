"""Build the standard ROM-free xdelta release and verify its Windows entry point."""
import argparse,csv,hashlib,json,os,shutil,subprocess,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
NAME='TinyToonAdventures_KR_Patch_v1.0_20261004'
PATCH='TinyToonAdventures_KR_v1.0_20261004.xdelta'
SOURCE_SHA='73300dc1505564827ef95ba3e2a06c26aa48920e4981195f32b2101c185ef3dd'
TARGET_SHA='6d834cdde925dd808ef6d911ebf2f13f5a88e440c9da4bfc50b424035309483d'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write_json(p,value):p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def windows_text(p,text,bom=True):p.write_bytes((b'\xef\xbb\xbf' if bom else b'')+text.replace('\r\n','\n').replace('\n','\r\n').encode('utf-8'))

def apply(folder,source,qa,destination=None):
    args=[str(folder/'apply.cmd')]+([] if source is None else [str(source)])+([] if destination is None else [str(destination)])
    assert not any('"' in s for s in args)
    command='"'+' '.join('"'+s+'"' for s in args)+'"'
    line='"'+os.environ.get('COMSPEC','cmd.exe')+'" /d /s /c '+command
    env=os.environ.copy();env['TT_PATCH_NO_PAUSE']='1'
    p=subprocess.run(line,cwd=qa,env=env,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=60)
    return {'command':line,'exit_code':p.returncode,'stdout':p.stdout.decode('utf-8',errors='replace'),'stderr':p.stderr.decode('utf-8',errors='replace')}

def check_apply(pkg,qa,source,target):
    qa.mkdir(parents=True,exist_ok=False)
    copy=qa/'패치 묶음';shutil.copytree(pkg,copy)
    original=qa/'원본 게임.nes';shutil.copyfile(source,original)
    output=qa/'원본 게임_KR.nes';checks={}
    checks['valid_apply']=apply(copy,original,qa);assert checks['valid_apply']['exit_code']==0,checks['valid_apply']
    assert output.read_bytes()==target.read_bytes()
    checks['existing_output']=apply(copy,original,qa);assert checks['existing_output']['exit_code']==1 and sha(output)==TARGET_SHA
    checks['same_source_and_output']=apply(copy,original,qa,original);assert checks['same_source_and_output']['exit_code']==1 and sha(original)==SOURCE_SHA
    wrong=qa/'別 판본.nes';bad=bytearray(source.read_bytes());bad[200]^=1;wrong.write_bytes(bad)
    checks['wrong_source_same_size']=apply(copy,wrong,qa);assert checks['wrong_source_same_size']['exit_code']==1 and not (qa/'別 판본_KR.nes').exists()
    checks['already_patched_source']=apply(copy,output,qa);assert checks['already_patched_source']['exit_code']==1 and not (qa/'원본 게임_KR_KR.nes').exists()
    corrupt=qa/'손상 패치';shutil.copytree(pkg,corrupt)
    patch=corrupt/PATCH;bad=bytearray(patch.read_bytes());bad[20]^=1;patch.write_bytes(bad)
    blocked=qa/'손상 패치 결과.nes';checks['corrupt_patch']=apply(corrupt,original,qa,blocked)
    assert checks['corrupt_patch']['exit_code']==1 and not blocked.exists()
    corrupt_tool=qa/'손상 도구';shutil.copytree(pkg,corrupt_tool)
    exe=corrupt_tool/'tools/xdelta3.exe';bad=bytearray(exe.read_bytes());bad[200]^=1;exe.write_bytes(bad)
    blocked=qa/'손상 도구 결과.nes';checks['corrupt_tool']=apply(corrupt_tool,original,qa,blocked)
    assert checks['corrupt_tool']['exit_code']==1 and not blocked.exists()
    checks['no_argument']=apply(copy,None,qa);assert checks['no_argument']['exit_code']==1
    assert not list(qa.glob('tinytoon_patch_*.tmp'))
    assert sha(original)==sha(source)==SOURCE_SHA
    report={'status':'PASS','checks':checks,'source_unchanged':True,'source_sha256':SOURCE_SHA,'output_sha256':sha(output),'byte_for_byte_target_match':True,'output_bytes':output.stat().st_size,'output':str(output.relative_to(ROOT)),'entrypoint_payload_sha256':{n:sha(pkg/n) for n in ['apply.cmd','apply.ps1',PATCH,'tools/xdelta3.exe']}}
    write_json(qa/'apply_verification.json',report)
    return report

def seal_package(out,qa,proof,source,target):
    archive=out.with_name(out.name+'.zip');hashfile=archive.with_suffix('.zip.sha256')
    assert not any(p.exists() for p in (archive,hashfile,proof))
    release=json.loads((out/'release_report.json').read_text(encoding='utf-8'))
    apply_report=json.loads((qa/'apply_verification.json').read_text(encoding='utf-8'))
    assert release['status']==apply_report['status']=='PASS' and release['source']['sha256']==SOURCE_SHA and release['target']['sha256']==TARGET_SHA
    assert len(apply_report['checks'])==8 and all(entry['exit_code']==(0 if name=='valid_apply' else 1) for name,entry in apply_report['checks'].items())
    for p,h in apply_report['entrypoint_payload_sha256'].items():assert sha(out/p)==h
    assert sha(source)==SOURCE_SHA and sha(target)==TARGET_SHA and release['patch']['sha256']==sha(out/PATCH)
    files=sorted(p for p in out.rglob('*') if p.is_file() and p.name!='SHA256.txt')
    checksum=''.join(f'{sha(p).upper()}  {p.relative_to(out).as_posix()}\r\n' for p in files).encode('utf-8')
    if (out/'SHA256.txt').exists() and (out/'SHA256.txt').stat().st_size:
        assert (out/'SHA256.txt').read_bytes()==checksum
    else:(out/'SHA256.txt').write_bytes(checksum)
    files=sorted(p for p in out.rglob('*') if p.is_file())
    expected={PATCH,'apply.cmd','apply.ps1','README_적용방법.txt','RELEASE_NOTES_KO.md','SHA256.txt','release_report.json','tools/xdelta3.exe','tools/README_xdelta3.md','tools/LICENSE_xdelta3.txt','licenses/Galmuri_OFL.md'}
    assert {p.relative_to(out).as_posix() for p in files}==expected
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in files:
            item=zipfile.ZipInfo((Path(out.name)/p.relative_to(out)).as_posix(),(2026,10,4,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;z.writestr(item,p.read_bytes())
    extracted=qa/'최종 ZIP 추출 final';extracted.mkdir()
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and set(z.namelist())=={(Path(out.name)/p.relative_to(out)).as_posix() for p in files}
        for p in files:assert z.read((Path(out.name)/p.relative_to(out)).as_posix())==p.read_bytes()
        z.extractall(extracted)
    final_source=extracted/'검증 원본.nes';shutil.copyfile(source,final_source)
    final_apply=apply(extracted/out.name,final_source,extracted)
    assert final_apply['exit_code']==0,final_apply
    final_output=extracted/'검증 원본_KR.nes';assert final_output.read_bytes()==target.read_bytes() and sha(final_source)==SOURCE_SHA
    for p in files:assert (extracted/out.name/p.relative_to(out)).read_bytes()==p.read_bytes()
    hashfile.write_text(f'{sha(archive).upper()}  {archive.name}\n',encoding='ascii')
    assert sha(source)==SOURCE_SHA
    result={'status':'PASS','package':out.relative_to(ROOT).as_posix(),'archive':archive.relative_to(ROOT).as_posix(),'archive_bytes':archive.stat().st_size,'archive_sha256':sha(archive),'source_sha256':SOURCE_SHA,'output_sha256':TARGET_SHA,'patch_sha256':sha(out/PATCH),'ROM_free':True,'ZIP_contents_exact':True,'contents_sha256':{p.relative_to(out).as_posix():sha(p) for p in files},'actual_Windows_apply_checks':8,'apply_report':(qa/'apply_verification.json').relative_to(ROOT).as_posix(),'apply_report_sha256':sha(qa/'apply_verification.json'),'final_ZIP_apply':final_apply,'final_ZIP_apply_byte_for_byte_target_match':True,'final_ZIP_payload_unchanged':True,'source_unchanged':True,'evidence_reuse':'Target ROM SHA identical; existing runtime/static/build evidence retained. Release changes packaging and xdelta apply path only.'}
    write_json(proof,result)
    print(json.dumps({'status':'PASS','archive':result['archive'],'archive_sha256':result['archive_sha256'],'patch_sha256':result['patch_sha256'],'files':len(files),'Windows_apply_checks':8,'final_ZIP_apply':'PASS'},ensure_ascii=False))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--name',default=NAME)
    ap.add_argument('--qa',type=Path,default=ROOT/'qa/apply/릴리즈 한글 경로 검증 20261004_001')
    ap.add_argument('--finish',action='store_true',help='Seal an assembled package only after its persisted eight-check apply report passes')
    a=ap.parse_args();assert a.name and Path(a.name).name==a.name and not a.name.endswith('.zip')
    out=ROOT/'dist'/a.name;archive=out.with_name(out.name+'.zip');hashfile=archive.with_suffix('.zip.sha256')
    qa=a.qa.resolve();qa.relative_to(ROOT/'qa/apply')
    proof=ROOT/'qa/reports'/f'release_{a.name}_final.json'
    source=ROOT/'original/rom/Tiny Toon Adventures (Japan).nes';build=ROOT/'build/dialogue_full_006';target=build/'TinyToon_dialogue_full.nes'
    if a.finish:
        seal_package(out,qa,proof,source,target);return
    assert not any(p.exists() for p in (out,archive,hashfile,qa,proof)),'Existing artifacts are protected'
    b=json.loads((build/'build_report.json').read_text(encoding='utf-8'))
    assert sha(source)==SOURCE_SHA and source.stat().st_size==262160 and sha(target)==TARGET_SHA and target.stat().st_size==524304
    assert b['output_sha256']==TARGET_SHA
    inputs={'workspace/translation/dialogue_ja.csv':'csv_sha256','workspace/fonts/galmuri7_8x8/Galmuri7_8x8.png':'font_png_sha256'}
    for p,key in inputs.items():assert sha(ROOT/p)==b[key]
    with (ROOT/'workspace/translation/dialogue_ja.csv').open(encoding='utf-8-sig',newline='') as f:rr=list(csv.DictReader(f))
    assert len(rr)==22 and all(r['status']=='needs_review' for r in rr)
    reports={}
    for kind in ('static','abi','stage_guard','runtime','cinema','visual','hamton','hamton_visual','scene_skip','scene_skip_visual'):
        p=ROOT/f'qa/reports/dialogue_full_006_{kind}.json';r=json.loads(p.read_text(encoding='utf-8'))
        assert r['status']=='PASS' and r.get('build_sha256',r.get('output_sha256'))==TARGET_SHA
        reports[kind]={'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
    previous=json.loads((ROOT/'qa/reports/dialogue_full_handoff_scene_skip_2026-10-04.json').read_text(encoding='utf-8'))
    for p,h in previous['protected_hashes'].items():assert sha(ROOT/p)==h,p
    xdelta=ROOT.parents[1]/'Tools/xdelta3-3.2.0-windows-x86_64/xdelta3.exe'
    xversion=subprocess.run([str(xdelta),'-V'],capture_output=True,check=True)
    assert b'3.2.0' in xversion.stdout+xversion.stderr
    (out/'tools').mkdir(parents=True);(out/'licenses').mkdir()
    shutil.copyfile(xdelta,out/'tools/xdelta3.exe')
    shutil.copyfile(xdelta.with_name('README.md'),out/'tools/README_xdelta3.md')
    shutil.copyfile(ROOT.parents[1]/'Games/Death Jr/tools/xdelta3-3.2.0/LICENSE',out/'tools/LICENSE_xdelta3.txt')
    shutil.copyfile(ROOT/'workspace/fonts/galmuri7_8x8/OFL.md',out/'licenses/Galmuri_OFL.md')
    subprocess.run([str(xdelta),'-e','-9','-S','none','-A','-s',str(source),str(target),str(out/PATCH)],check=True)
    patch_sha=sha(out/PATCH)
    substitutions={'@SOURCE_SHA@':SOURCE_SHA,'@TARGET_SHA@':TARGET_SHA,'@PATCH_NAME@':PATCH,'@PATCH_SHA@':patch_sha,'@XDELTA_SHA@':sha(xdelta)}
    helper=(ROOT/'workspace/release/apply_xdelta.ps1.in').read_text(encoding='utf-8')
    for old,new in substitutions.items():helper=helper.replace(old,new)
    assert '@SOURCE_SHA@' not in helper
    windows_text(out/'apply.ps1',helper)
    windows_text(out/'apply.cmd',(ROOT/'workspace/release/apply.cmd.in').read_text(encoding='utf-8'),bom=False)
    notes=(ROOT/'workspace/release/RELEASE_NOTES_KO.md').read_text(encoding='utf-8').replace(NAME+'.zip',a.name+'.zip')
    (out/'RELEASE_NOTES_KO.md').write_text(notes,encoding='utf-8')
    windows_text(out/'README_적용방법.txt',f'''========================================================================
 타이니 툰 어드벤처스 한글 패치 v1.0 (2026-10-04)
 대상: Tiny Toon Adventures (Japan) / NES, Famicom
========================================================================

[구성]
{PATCH} : 타이틀 로고 및 일본어 대사22블록 통합 xdelta 패치
apply.cmd / apply.ps1 : Windows 원본 확인 및 패치 적용 도구
tools/xdelta3.exe : xdelta 3.2.0 Windows x64
SHA256.txt : 배포 파일 체크섬
release_report.json : 지원 원본/결과 해시와 적용·QA 범위
RELEASE_NOTES_KO.md : 릴리즈 안내
licenses/Galmuri_OFL.md : 사용 글꼴 고지
tools/README_xdelta3.md / tools/LICENSE_xdelta3.txt : 적용 도구 고지

원본 ROM 및 패치 완료 ROM은 포함하지 않습니다.

[적용 방법]
1. ZIP을 폴더에 모두 풉니다. tools 폴더도 함께 유지하세요.
2. 아래 SHA-256과 일치하는 일본판 원본 .nes를 준비합니다.
3. 원본 .nes를 apply.cmd 위로 끌어다 놓습니다.
4. 원본과 같은 폴더에 <원본 파일명>_KR.nes가 생성됩니다.
   원본은 변경하지 않으며 기존 결과 파일도 덮어쓰지 않습니다.

명령 프롬프트: apply.cmd "Tiny Toon Adventures (Japan).nes"
새 결과 경로 지정: apply.cmd "원본.nes" "새 경로\\결과_KR.nes"
Windows x64와 기본 Windows PowerShell이 필요하며 Python은 필요 없습니다.
다른 판본/이미 수정한 ROM/헤더 표현이 다른 파일은 지원하지 않습니다.

지원 원본 크기: 262,160바이트
지원 원본 SHA-256: {SOURCE_SHA.upper()}
완성 ROM 크기: 524,304바이트
완성 ROM SHA-256: {TARGET_SHA.upper()}

[한글화 범위]
타이틀 로고, 도입부 이야기/대사, 셜리 선택 안내와 파트너 추천,
햄튼 당근 교환/부족 안내, 엔딩4문단. 글꼴은 Galmuri7 8×8입니다.
기존 영문 표기와 스태프롤은 유지했습니다. 번역은 사용자 제공22블록입니다.

[검증 범위]
정적/코드 모델/재빌드/패치 적용을 통과한 dialogue_full_006과 같은 결과입니다.
Mesen2.1.1에서 정상 도입부와 캐릭터 선택, 실제 햄튼30개 교환 및
별도 카운터29개 부족 분기, 6개 스테이지 선택과 실제 엔딩/스태프롤을 확인했습니다.
6개 선택과 실제 엔딩은 장면 스킵으로 실행했으며 해당631개 비교 화면에서
대사 영역 밖 픽셀 차이는0입니다. 전체 완주를 수행한 검증은 아닙니다.
실기/다른 에뮬레이터와 전 게임 RAM 조사는 미수행입니다.
번역 CSV의22개 needs_review는 그대로이며 최종 문구/화자 검토 완료로 표기하지 않습니다.
배포본의 실제 apply.cmd 적용/잘못된 원본·기존 결과·손상 패치·손상 도구 거부와
ZIP을 푼 뒤의 적용 결과를 검증했습니다. 상세 결과는 release_report.json을 따릅니다.

[글꼴과 도구]
Galmuri7: Copyright 2019–2025 Lee Minseo, SIL Open Font License1.1.
xdelta3: Copyright Joshua MacDonald, Apache License2.0.
동봉 라이선스와 고지를 참조하세요. 글꼴 PNG/TTF와 에뮬레이터는 포함하지 않습니다.
비공식 팬 번역 패치이며 게임/캐릭터/상표의 권리는 각 권리자에게 있습니다.
문제 제보에는 장면, 사용 환경과 버전, 화면, 원본/결과 SHA-256을 함께 기록하세요.
''')
    release={'name':a.name,'version':'1.0','date':'2026-10-04','status':'ASSEMBLED_APPLY_PENDING','format':'Standard game distribution: xdelta, apply.cmd/apply.ps1, Korean README, SHA256, release report, tool/license material, ZIP with one release-root folder','source':{'file':'Tiny Toon Adventures (Japan).nes','bytes':262160,'sha256':SOURCE_SHA},'target':{'bytes':524304,'sha256':TARGET_SHA,'build':'dialogue_full_006'},'patch':{'file':PATCH,'bytes':(out/PATCH).stat().st_size,'sha256':patch_sha},'xdelta':{'version':'3.2.0','sha256':sha(xdelta)},'translated_blocks':22,'font':'Galmuri7 native8x8','CSV_sha256':b['csv_sha256'],'CSV_needs_review':22,'translation_review':'User-supplied translation; existing review statuses retained. Final editorial sign-off not recorded. User authorized release packaging.','verification_reports':reports,'runtime':{'emulator':'Mesen2.1.1','normal_intro_blocks':6,'Hamton_blocks':5,'Hamton29_branch':'one declared counter RAM write; normal30 collection/exchange separate','six_stage_selection_and_real_ending':'declared RAM-only original-dispatcher scene skips','scene_skip_comparison_samples':631,'outside_text_pixel_differences':0,'direct_visual_review':'PASS, recorded separately'},'accepted_difference':'JP_1780B eight middle pauses redistributed for Korean; first/final hold, count and completion timing retained','unperformed':['full playthrough/final-boss victory','hardware','other emulators','whole-game RAM ownership audit','final editorial sign-off'],'ROM_free':True,'runtime_scene_skip_tools_included':False}
    write_json(out/'release_report.json',release)
    apply_report=check_apply(out,qa,source,target)
    release['status']='PASS';release['apply_verification']={'status':'PASS','checks':{name:('PASS' if entry['exit_code']==(0 if name=='valid_apply' else 1) else 'FAIL') for name,entry in apply_report['checks'].items()},'source_unchanged':True,'byte_for_byte_target_match':True,'unicode_space_paths':True,'tested_payload_sha256':apply_report['entrypoint_payload_sha256']}
    write_json(out/'release_report.json',release)
    seal_package(out,qa,proof,source,target)

if __name__=='__main__':main()
