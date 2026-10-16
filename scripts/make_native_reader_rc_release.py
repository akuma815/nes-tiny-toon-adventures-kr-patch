"""Package candidate011 in the established eleven-file xdelta release layout."""
import hashlib,json,shutil,subprocess
from pathlib import Path
import make_release_dist as common
ROOT=Path(__file__).resolve().parents[1]
NAME='TinyToonAdventures_KR_Patch_v1.0.1-rc1_20261004'
PATCH='TinyToonAdventures_KR_v1.0.1-rc1_20261004.xdelta'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    src=ROOT/'original/rom/Tiny Toon Adventures (Japan).nes';build=ROOT/'build/dialogue_native_011';target=build/'TinyToon_dialogue_full.nes'
    b=json.loads((build/'build_report.json').read_text());assert sha(src)==b['source_sha256'] and sha(target)==b['output_sha256']
    reports={}
    for kind in ['static','abi','runtime','visual']:
        p=ROOT/f'qa/reports/dialogue_native_011_{kind}.json';r=json.loads(p.read_text(encoding='utf-8'))
        assert r['status']=='PASS' and r.get('rom_sha256',r.get('output_sha256'))==b['output_sha256']
        reports[kind]={'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
    out=ROOT/'dist'/NAME;qa=ROOT/'qa/apply/수정 후보 릴리즈 한글 경로 검증 20261004_001';proof=ROOT/f'qa/reports/release_{NAME}_final.json'
    assert not out.exists() and not qa.exists() and not proof.exists()
    (out/'tools').mkdir(parents=True);(out/'licenses').mkdir()
    vendor=ROOT/'dist/TinyToonAdventures_KR_Patch_v1.0_20261004'
    for name in ['tools/xdelta3.exe','tools/README_xdelta3.md','tools/LICENSE_xdelta3.txt','licenses/Galmuri_OFL.md']:
        shutil.copy2(vendor/name,out/name)
    tool=out/'tools/xdelta3.exe'
    subprocess.run([str(tool),'-e','-9','-S','none','-A','-s',str(src),str(target),str(out/PATCH)],check=True)
    values={'@SOURCE_SHA@':sha(src),'@TARGET_SHA@':sha(target),'@PATCH_NAME@':PATCH,'@PATCH_SHA@':sha(out/PATCH),'@XDELTA_SHA@':sha(tool)}
    text=(ROOT/'workspace/release/apply_xdelta.ps1.in').read_text(encoding='utf-8')
    for old,new in values.items():text=text.replace(old,new)
    common.windows_text(out/'apply.ps1',text)
    common.windows_text(out/'apply.cmd',(ROOT/'workspace/release/apply.cmd.in').read_text(encoding='utf-8'),bom=False)
    notes=(ROOT/'workspace/release/RELEASE_NOTES_NATIVE_RC_KO.md').read_text(encoding='utf-8')
    (out/'RELEASE_NOTES_KO.md').write_text(notes,encoding='utf-8')
    common.windows_text(out/'README_적용방법.txt',f'''타이니 툰 어드벤처스 한글 패치 v1.0.1-rc1 (2026-10-04)

당근 교환 대사 문제 수정 후보입니다. 제보 사진의 깨짐은 같은 조건으로
재현하지 못했으므로 해결 확정본으로 표기하지 않습니다.

수정: 893바이트 대사를 원래 일본어 영역974바이트 안에 직접 넣고
원본 대사 읽기 코드를 복원했습니다. Galmuri7 8×8의 '몇' 획을 분리했습니다.
원본 ROM·번역 CSV·지정 폰트 PNG를 변경하지 않았습니다.

ZIP을 모두 풀고 아래 해시의 일본판 원본 NES ROM을 준비하세요.
기존 한글 ROM에 덧씌우지 말고 원본에 새로 적용합니다.
기존 파일을 보존하려면 새 결과 이름을 지정하세요:

apply.cmd "Tiny Toon Adventures (Japan).nes" "TinyToonAdventures_KR_v1.0.1_rc1.nes"

또는 원본을 apply.cmd 위에 끌어 놓으면 같은 폴더에 <원본명>_KR.nes가
생성됩니다. 이미 있는 결과는 덮어쓰지 않습니다. Windows x64와 기본
Windows PowerShell이 필요하며 Python은 필요 없습니다.

새 ROM을 처음부터 부팅하여 확인하세요. 이전 빌드의 저장 상태는
대사 주소가 달라 호환되지 않습니다. 새 ROM의 타이틀부터 진행합니다.

원본: 262160바이트 / SHA-256 {sha(src).upper()}
결과: 524304바이트 / SHA-256 {sha(target).upper()}

구성은 기존 릴리즈와 동일합니다: xdelta, apply.cmd/apply.ps1, 설명서,
릴리즈 글, SHA256.txt, release_report.json, tools/, licenses/.
ROM·폰트 PNG/TTF·에뮬레이터는 포함하지 않습니다.

정적/CPU모델/재빌드와 Windows 적용을 검증했습니다. Mesen2.2.1에서
30개 실제 교환 및 카운터1개 부족 분기, 자연 도입부, 6개 선택 화면,
실제 엔딩과 스태프롤을 확인했습니다. 선택/엔딩은 원래 장면 처리기로
넘기는 명시적 RAM 스킵이며 전체 완주는 아닙니다. Mesen2.1.1의 부족
화면도 확인했습니다. 자세한 표본/범위는 release_report.json을 참조하세요.
CSV22개 needs_review와 미수행 실기/전체 완주/문구 최종 검토를 유지합니다.

Galmuri7: Copyright 2019–2025 Lee Minseo, SIL Open Font License1.1.
xdelta3: Copyright Joshua MacDonald, Apache License2.0. 동봉 고지를 참조하세요.
비공식 팬 번역이며 게임/캐릭터/상표의 권리는 각 권리자에게 있습니다.
''')
    release={'name':NAME,'version':'1.0.1-rc1','date':'2026-10-04','status':'ASSEMBLED_APPLY_PENDING','fix_status':'USER_REPORTED_CORRUPTION_RETEST_PENDING','source':{'file':src.name,'bytes':src.stat().st_size,'sha256':sha(src)},'target':{'bytes':target.stat().st_size,'sha256':sha(target),'build':'dialogue_native_011'},'patch':{'file':PATCH,'bytes':(out/PATCH).stat().st_size,'sha256':sha(out/PATCH)},'verification_reports':reports,'translated_blocks':22,'CSV_needs_review':22,'font':'Supplied Galmuri7 native8x8; explicit few-glyph override','glyph_override_sha256':b['glyph_override_sha256'],'runtime_scope':'Mesen2.2.1 natural intro; native Hamton30 / one counter1 write; six selection/ending scenes via original dispatcher RAM skips. Mesen2.1.1 insufficient caption smoke.','user_screenshot_regression':'Not independently reproduced in006. Native reader restored in011 and complete text pixels verified in declared captures; user condition retest pending.','old_savestate_compatibility':False,'unperformed':['full playthrough','hardware','final translation review','reproduction of the exact user screenshot condition'],'ROM_free':True}
    common.write_json(out/'release_report.json',release)
    common.NAME=NAME;common.PATCH=PATCH;common.SOURCE_SHA=sha(src);common.TARGET_SHA=sha(target)
    apply=common.check_apply(out,qa,src,target)
    release['status']='PASS';release['status_scope']='Packaging/apply and the explicitly listed QA gates; bug-resolution status is fix_status'
    release['apply_verification']={'status':'PASS','checks':8,'source_unchanged':True,'byte_for_byte_target_match':True,'unicode_space_paths':True,'entrypoint_payload_sha256':apply['entrypoint_payload_sha256']}
    common.write_json(out/'release_report.json',release)
    common.seal_package(out,qa,proof,src,target)
    result=json.loads(proof.read_text());result['evidence_reuse']='New011 static/ABI/runtime/visual reports; independent candidate QA. Old006 runtime conclusions are historical.';result['fix_status']=release['fix_status'];common.write_json(proof,result)
if __name__=='__main__':main()
