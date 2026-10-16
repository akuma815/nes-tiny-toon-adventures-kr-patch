"""Ship the verified farewell-font fix in the established release layout."""
import hashlib,json,shutil,subprocess
from pathlib import Path
import make_release_dist as common
ROOT=Path(__file__).resolve().parents[1]
NAME='TinyToonAdventures_KR_Patch_v1.0.1_20261004'
PATCH='TinyToonAdventures_KR_v1.0.1_20261004.xdelta'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    src=ROOT/'original/rom/Tiny Toon Adventures (Japan).nes';build=ROOT/'build/dialogue_footer_fix_003';target=build/'TinyToon_dialogue_full.nes'
    b=json.loads((build/'build_report.json').read_text());assert sha(src)==b['source_sha256'] and sha(target)==b['output_sha256']
    reports={}
    for kind in ['static','abi','runtime','visual']:
        p=ROOT/f'qa/reports/dialogue_footer_003_{kind}.json';r=json.loads(p.read_text(encoding='utf-8'))
        assert r['status']=='PASS' and r.get('rom_sha256',r.get('output_sha256'))==b['output_sha256']
        reports[kind]={'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
    out=ROOT/'dist'/NAME;qa=ROOT/'qa/apply/당근 수정 릴리즈 한글 경로 검증_20261004_001';proof=ROOT/f'qa/reports/release_{NAME}_final.json'
    assert not out.exists() and not qa.exists() and not proof.exists()
    (out/'tools').mkdir(parents=True);(out/'licenses').mkdir()
    vendor=ROOT/'dist/TinyToonAdventures_KR_Patch_v1.0_20261004'
    for name in ['tools/xdelta3.exe','tools/README_xdelta3.md','tools/LICENSE_xdelta3.txt','licenses/Galmuri_OFL.md']:shutil.copy2(vendor/name,out/name)
    tool=out/'tools/xdelta3.exe'
    subprocess.run([str(tool),'-e','-9','-S','none','-A','-s',str(src),str(target),str(out/PATCH)],check=True)
    values={'@SOURCE_SHA@':sha(src),'@TARGET_SHA@':sha(target),'@PATCH_NAME@':PATCH,'@PATCH_SHA@':sha(out/PATCH),'@XDELTA_SHA@':sha(tool)}
    text=(ROOT/'workspace/release/apply_xdelta.ps1.in').read_text(encoding='utf-8')
    for old,new in values.items():text=text.replace(old,new)
    common.windows_text(out/'apply.ps1',text)
    common.windows_text(out/'apply.cmd',(ROOT/'workspace/release/apply.cmd.in').read_text(encoding='utf-8'),bom=False)
    notes='''# 타이니 툰 어드벤처스 한글 패치 v1.0.1 (2026-10-04)

당근 30개 교환 후 “그럼 몇 개인지 / 세어 볼게”가 남아 있는 동안 다음 대사의 폰트가 먼저 적용되는 문제를 고쳤습니다. 사용자 사진의 “.아 쉽 지만당 / 근이 조금”과 같은 잘못된 출력을 기존 v1.0 ROM에서 재현했습니다. 공통 작별 대사의 대기 구간에는 실제로 표시 중인 폰트를 유지합니다. 부족 안내와 작별 대사 전체 출력도 확인했습니다.

Galmuri7 8×8의 ‘몇’ 한 글자만 획을 분리하여 가독성을 개선했습니다. 원본 폰트 PNG와 번역 CSV, 대사 주소·읽기 구조는 보존했습니다.

Mesen2.2.1과2.1.1에서 정상 교환·당근 부족 및 작별 대기 구간을 확인했습니다. 자연 도입부, 여섯 선택 화면과 실제 엔딩 처리기로 진입한 대사22블록도 검증했습니다. 선택·엔딩은 명시적 RAM 장면 스킵이며 전체 완주를 뜻하지 않습니다. 정적/CPU 모델/재빌드/IPS 및 실제 Windows xdelta 적용 검증을 분리해 기록했습니다.

일본판 원본에 새로 패치하고 새 이름의 ROM을 처음부터 실행하세요. 문제가 발생한 대화 도중의 이전 저장 상태는 화면·폰트 상태를 다시 가져올 수 있으므로 확인에 사용하지 마세요. 전체 완주·실기·번역 문구와 화자의 최종 검토는 미수행이며 CSV22개 needs_review를 유지합니다.

기존 배포와 동일한11파일 구성입니다. ROM과 폰트 PNG/TTF, 에뮬레이터는 포함하지 않습니다. Galmuri의 SIL OFL1.1 및 xdelta3의 Apache2.0 고지는 동봉했습니다.
'''
    (out/'RELEASE_NOTES_KO.md').write_text(notes,encoding='utf-8')
    common.windows_text(out/'README_적용방법.txt',f'''타이니 툰 어드벤처스 한글 패치 v1.0.1

ZIP을 모두 압축 해제하고 일본판 원본 ROM에 적용하세요.
Windows x64 / 기본 Windows PowerShell을 사용합니다. Python은 필요 없습니다.

apply.cmd "Tiny Toon Adventures (Japan).nes" "TinyToonAdventures_KR_v1.0.1.nes"

원본을 apply.cmd에 끌어 놓아도 됩니다. 기본 출력은 원본 이름 뒤에 _KR입니다.
이미 있는 출력 파일을 덮어쓰지 않습니다. 이전 한글 ROM에 중복 적용하지 마세요.
새 ROM을 처음부터 실행하고 이전의 문제 대화 저장 상태를 불러오지 마세요.

원본: 262160바이트 / SHA-256 {sha(src).upper()}
결과: 524304바이트 / SHA-256 {sha(target).upper()}

수정 내용과 검증 범위는 RELEASE_NOTES_KO.md 및 release_report.json을 참고하세요.
구성: xdelta, apply.cmd/apply.ps1, 설명서/릴리즈 글, SHA256.txt,
release_report.json, tools/, licenses/. ROM은 포함하지 않습니다.
Galmuri7: Copyright 2019–2025 Lee Minseo, SIL Open Font License1.1.
xdelta3: Copyright Joshua MacDonald, Apache License2.0. 동봉 고지를 참고하세요.
비공식 팬 번역이며 게임과 캐릭터의 권리는 각 권리자에게 있습니다.
''')
    release={'name':NAME,'version':'1.0.1','date':'2026-10-04','status':'ASSEMBLED_APPLY_PENDING','fix_status':'REPRODUCED_AND_VERIFIED','source':{'file':src.name,'bytes':src.stat().st_size,'sha256':sha(src)},'target':{'bytes':target.stat().st_size,'sha256':sha(target),'build':build.name},'patch':{'file':PATCH,'bytes':(out/PATCH).stat().st_size,'sha256':sha(out/PATCH)},'verification_reports':reports,'translated_blocks':22,'CSV_needs_review':22,'font':'Supplied Galmuri7 8x8; explicit few-glyph override','glyph_override_sha256':b['glyph_override_sha256'],'runtime_scope':'Mesen2.2.1 natural intro and Hamton30; one counter1 write; six selection/ending scenes via original dispatcher RAM skips. Both Hamton branches also Mesen2.1.1. Captured wait frames checked pixel by pixel.','root_cause':'Counting nametable survived root18 F7 wait while linear address selector loaded skipped insufficient-page font. Preserve actual cached font until cursor6.','architecture':'006 reader/data addresses/IRQ cache retained','unperformed':['full playthrough','hardware','final translation and speaker review'],'ROM_free':True}
    common.write_json(out/'release_report.json',release)
    common.NAME=NAME;common.PATCH=PATCH;common.SOURCE_SHA=sha(src);common.TARGET_SHA=sha(target)
    apply=common.check_apply(out,qa,src,target)
    release['status']='PASS';release['apply_verification']={'status':'PASS','checks':8,'source_unchanged':True,'byte_for_byte_target_match':True,'unicode_space_paths':True,'entrypoint_payload_sha256':apply['entrypoint_payload_sha256']}
    common.write_json(out/'release_report.json',release);common.seal_package(out,qa,proof,src,target)
    result=json.loads(proof.read_text(encoding='utf-8'));result['evidence_reuse']='New footer003 static/ABI/runtime/visual QA; old006 capture used solely as the reproduced defect reference.';result['fix_status']=release['fix_status'];common.write_json(proof,result)
if __name__=='__main__':main()
