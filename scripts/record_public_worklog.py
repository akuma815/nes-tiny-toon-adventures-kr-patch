"""Record the public article without changing prior game-build evidence."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    package=ROOT/'workspace/publication/TinyToon_KR_Worklog_NaverCafe_20261004.zip'
    folder=ROOT/'workspace/publication/TinyToon_KR_Worklog_20261004_002'
    report=ROOT/'qa/reports/TinyToon_KR_Worklog_20261004_002_publication.json';r=json.loads(report.read_text(encoding='utf-8'));assert r['status']=='PASS' and sha(package)==r['archive']['sha256']
    for name,h in r['public_files'].items():assert sha(folder/name)==h,name
    checked=set()
    for name in ['dialogue_release_handoff_2026-10-04.json','dialogue_footer_handoff_2026-10-04.json']:
        old=json.loads((ROOT/'qa/reports'/name).read_text(encoding='utf-8'))
        for path,h in old['artifact_hashes'].items():
            if path.startswith('docs/') or path in checked:continue
            assert sha(ROOT/path)==h,path;checked.add(path)
    paragraph='**2026-10-04 작업18 최신:** 네이버 카페용 [한글화 작업기](PUBLIC_WORKLOG_2026-10-04.md)를 작성했다. 실제 캡처·폰트 확대·구조도16장, 복사용 본문, 이미지 내장 HTML, 업로드 안내를 묶었다. 게임 패치는 작업17의 v1.0.1을 유지하며 이번 작업은 게시 자료 제작·문서/브라우저 검증만 수행했다.'
    p=ROOT/'docs/HANDOFF.md';t=p.read_text(encoding='utf-8');assert paragraph not in t;lines=t.splitlines(keepends=True);p.write_text(lines[0]+'\n'+paragraph+'\n\n'+''.join(lines[1:]),encoding='utf-8')
    detail=f'''# 네이버 카페용 한글화 작업기 — 2026-10-04 작업18

사용자가 인터넷 게시판에 공유할 읽기 쉬운 작업기를 요청했고, 대상 게시판은 네이버 카페로 지정했다. 로고 제작부터 대사 추출·8×8 폰트·전체 삽입·당근 교환 오류 수정·검증·차분 배포까지 실제 기록으로 구성했다.

## 최신 산출물

- [업로드용 ZIP](../workspace/publication/TinyToon_KR_Worklog_NaverCafe_20261004.zip): 19파일, {r['archive']['bytes']:,}바이트. 본문1·HTML1·업로드안내1·PNG16.
- [이미지를 내장한 읽기용 완성본](../workspace/publication/TinyToon_KR_Worklog_20261004_002/작업기.html): 파일 하나로 읽기 가능. 이미지 확대/Esc닫기, 엔딩 접기, 모바일 문단 배치.
- [네이버 카페 복사용 본문](../workspace/publication/TinyToon_KR_Worklog_20261004_002/네이버카페_게시글본문.txt): UTF-8 BOM, 이미지01~16 삽입 위치와 설명 일치.
- [이미지 폴더](../workspace/publication/TinyToon_KR_Worklog_20261004_002/images/), [업로드 안내](../workspace/publication/TinyToon_KR_Worklog_20261004_002/업로드안내.txt).
- [자료·원본 귀속·검증 보고서](../qa/reports/TinyToon_KR_Worklog_20261004_002_publication.json), [PC/모바일 렌더 보고서](../qa/publication/TinyToon_worklog_render_004/render_report.json).

본문은 v1.0.1의22블록 삽입/실제 출력과 제시한 검증 범위를 설명한다. 원문·타이틀·오류 캡처는 각각 이전 기준선으로 구분했다. 게임 화면의 글자를 다시 그리지 않았으며 화면 합성은 정수 배율 최근접 확대다. 격자 오버레이, 글리프 확대, CSV 재구성, 구조도는 설명용 자료로 표시했다. 생성형AI 사용은 기존 타이틀 시안 제작에 귀속하고, 실제 게임 캡처와 구분했다. 화자 메타데이터의 확정/유력 구분과 공식 한국어명 미인증 상태를 설명했다.

## 시각자료16장

1. 현재 타이틀과 작업 범위 표지
2. 작업 흐름 구조도
3. 로고 변경 전후
4. 원문·번역·화자 CSV 예시
5. 8×8 글자·16열×7행 영역 설명
6. 문단별 폰트와 동일 코드0x70의 다른 글자
7. ‘몇’의 원래 글리프/삽입 글리프 비교
8. 셜리 원문·한글 화면 비교
9. 선택·조작 안내4장면
10. 당근 교환·부족·작별4장면
11. 기존006 오류와 수정본의 실제 대기 캡처 비교
12. 정상/부족 분기의 공통 대기 폰트 구조도
13. 자연 도입부4장면
14. 정적/빌드·적용/실행/시각 검증 구분도
15. xdelta 적용 및11파일 배포 구성도
16. 엔딩4장면 — 결말 스포일러, HTML에서는 접힘

## 검증 구분

문서/정적: 실제 증거에 연결한 모든 이미지·데이터 원본SHA와 16PNG SHA 확인. 본문 이미지 표식01~16과 실제 파일명 순서 일치, HTML 내장PNG와 개별파일 바이트 동일, UTF-8 대체문자 없음. 전체완주/실기/최종번역검토를 완료로 표기하지 않는다. 두Mesen의 검증범위도 구분해2.2.1은22블록,2.1.1은교환두분기 재확인으로 적었다.

자료 생성/압축: ZIP CRC/19파일/실제payload 동일성 PASS. ROM·전체폰트·덤프·에뮬레이터를 포함하지 않았다. 기존 패치ZIP은 변경하거나 작업기ZIP에 재포장하지 않았다.

브라우저 실행: 격리 headless Edge에서1280×1000 및390×844 화면,16이미지 디코딩,본문 가로넘침 없음, 이미지확대/실제Esc닫기/엔딩접기 개폐 PASS. [PC](../qa/publication/TinyToon_worklog_render_004/desktop_top.png), [모바일](../qa/publication/TinyToon_worklog_render_004/mobile_top.png), [PC 오류 설명](../qa/publication/TinyToon_worklog_render_004/desktop_bug_section.png), [모바일 오류 설명](../qa/publication/TinyToon_worklog_render_004/mobile_bug_section.png) 캡처를 직접 검토했다. JavaScript 오류0, 외부이미지 의존0.

직접 시각:16그림의 글씨·일본어/한국어·화살표·수정전후·영역표시·장면캡처를 확인했다. PC/모바일 읽기용 페이지도 확인했고 모바일 제목의 단어중간 줄바꿈을 수정했다. 작은 이미지의 세부는 HTML의 확대보기 또는 개별PNG로 확인한다.

게임 빌드/패치 적용/에뮬레이터 실행: **이번 게시 자료 작업에서는 미수행.** 작업17의 기존 v1.0.1 검증 증거를 인용한다. 원본·CSV·폰트·ROM·차분 패치·이전QA를 수정하지 않았다. 이전 감사에 등록된 문서 외 {len(checked):,}개 파일의SHA를 보존 확인했다.

미수행: 실제 네이버 카페 업로드/게시, 카페 편집기에서의 게시 후 배치 확인. 게시 주소와 제작자 이름은 지정받지 않았으며 임의로 넣지 않았다. 독립된 읽기용HTML은 카페 편집기에 HTML코드를 붙이는 용도가 아니다. 본문과PNG를 따로 올리는 형식으로 제공했다.

## 변경 파일·해시·재현

작성/생성 스크립트는 [make_public_worklog.py](../scripts/make_public_worklog.py), [render_public_worklog.py](../scripts/render_public_worklog.py), [seal_public_worklog.py](../scripts/seal_public_worklog.py), [record_public_worklog.py](../scripts/record_public_worklog.py)다. 원본게임PNG·CSV·빌드pages·기존QA보고서는 읽기만 했다. 출처와이미지별SHA는 자료 보고서, 새파일 해시는 최종 [게시 자료 인계 감사](../qa/reports/TinyToon_worklog_handoff_20261004.json)에 기록한다.

| 대상 | SHA-256 |
|---|---|
| 작업기 ZIP | `{sha(package)}` |
| HTML | `{sha(folder/'작업기.html')}` |
| 카페 본문 | `{sha(folder/'네이버카페_게시글본문.txt')}` |
| 자료 보고서 | `{sha(report)}` |
| 기존 게임 ROM | `d57b816fce99d99eb700ebecc3d2397a1d039418ead3b1233d720c712fb2df3d` |

프로젝트루트/Python3.12/Pillow/Windows 맑은고딕·MS Gothic와 기존 캡처/CSV/pages가 필요하다. 브라우저 검사는 Windows Edge와 websocket-client를 사용하며 사용자 브라우저 프로필을 조작하지 않는다. 렌더 출력에는 각자 격리 프로필을 생성한다. 사용자에게 공유하는ZIP에는 설치폰트·브라우저프로필·QA가 없다.

```powershell
python scripts/make_public_worklog.py --output workspace/publication/TinyToon_worklog_repro_next
python scripts/render_public_worklog.py --input workspace/publication/TinyToon_worklog_repro_next/작업기.html --output qa/publication/TinyToon_worklog_render_next
```

새 출력 경로를 사용한다. 생성 후 시각 검토를 마친 후보만 seal_public_worklog.py로 봉인한다. `--finish`는 CRC와payload가 이미 일치하는 미완료ZIP의 메타데이터를 마무리하는 옵션이며 기존ZIP을 덮어쓰지 않는다. _001은초안, render002는비어있는 확대창이미지까지decode하려던검사 실패, render003은수정후통과, render004는모바일제목수정후최종통과 이력으로 보존했다. 이들은 게임의 글자 깨짐 재현과 무관하다.

**다음 작업 하나: 네이버 카페 글쓰기에서 복사용 본문을 붙이고 표식 위치에 번호순PNG를 첨부하여 게시한다.**
'''
    (ROOT/'docs/PUBLIC_WORKLOG_2026-10-04.md').write_text(detail,encoding='utf-8')
    p=ROOT/'docs/HANDOFF_2026-10-04.md';t=p.read_text(encoding='utf-8');assert '## 작업18 —' not in t;p.write_text(t+'\n\n## 작업18 — 네이버 카페용 시각자료 작업기\n\n'+paragraph+'\n\n'+detail[detail.index('## 최신 산출물'):],encoding='utf-8')
    auditpath=ROOT/'qa/reports/TinyToon_worklog_handoff_20261004.json';assert not auditpath.exists();auditpath.write_text('{}\n',encoding='utf-8')
    links=[];bad=[]
    for p in (ROOT/'docs').glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            target=target.strip('<>').split('#')[0]
            if not target or '://' in target:continue
            q=(p.parent/target).resolve();links.append((p.name,target))
            if not q.exists():bad.append((p.name,target))
    assert not bad,bad
    paths=[package,package.with_suffix('.zip.sha256'),report,ROOT/'docs/PUBLIC_WORKLOG_2026-10-04.md',ROOT/'docs/HANDOFF.md',ROOT/'docs/HANDOFF_2026-10-04.md']
    paths.extend(folder.rglob('*'))
    paths.extend((ROOT/'scripts'/name) for name in ['make_public_worklog.py','render_public_worklog.py','seal_public_worklog.py','record_public_worklog.py'])
    paths.extend(p for p in (ROOT/'qa/publication/TinyToon_worklog_render_004').iterdir() if p.is_file())
    hashes={p.relative_to(ROOT).as_posix():sha(p) for p in paths if p.is_file()}
    audit={'status':'PASS','work':18,'archive_sha256':sha(package),'source_build_unchanged':True,'old_non_doc_files_SHA_verified':len(checked),'local_markdown_links_verified':len(links),'artifact_hashes':hashes,'validation_scope':'Publication structure, payload, provenance, local browser/UI and direct visual; game tests reused from work17.','next_action':'Upload cafe plaintext and numbered PNG at marked positions; ending warning retained.'}
    auditpath.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':'PASS','links':len(links),'preserved':len(checked),'artifacts':len(hashes)}))
if __name__=='__main__':main()
