# Tiny Toon Adventures — NES 한글화

**2026-10-04 작업 16 최신:** 기존 배포 폴더와 같은 구성으로 [한글 패치 v1.0 릴리즈](docs/RELEASE_2026-10-04.md)를 작성했다. [정식 ZIP](dist/TinyToonAdventures_KR_Patch_v1.0_20261004.zip)은 xdelta·Windows 적용 도구·한국어 설명서/릴리즈 글·체크섬·검증 보고서·도구/폰트 라이선스의11파일이며 ROM은 포함하지 않는다. 실제 Windows 적용8검사와 최종ZIP추출후적용이PASS이고 결과는 기존006과바이트단위로같다. 등록22블록의장면출력증거와선택/실제엔딩631표본QA는유지했다. CSV22개`needs_review`와이전빌드/QA/테스트002를보존했다. 전체완주/실기/다른에뮬레이터와최종문구검토를완료로표기하지않는다. 아래항목은이전이력이며오늘인계작업16을따른다.

**2026-10-04 작업 10 이력:** [셜리 조작 안내](docs/DIALOGUE_THREE.md)를 추가해 현재 **3/22블록**이다. [검증 ROM](build/dialogue_three_001/TinyToon_dialogue_three.nes)에서 방향키/A 선택과 폰트 복귀를 확인했다. 44프레임 대사창 밖 차이0, 재빌드/IPS적용 동일. 다음은 `JP_1760C` ‘그럼 또 봐’ 삽입이며 재개는 [오늘 인계 작업10](docs/HANDOFF_2026-10-04.md)을 따른다. 아래 두 페이지 기록은 작업9 이력이다.

**2026-10-04 작업 9 이력:** [페이지별 한글 폰트 공급](docs/DIALOGUE_PAGED.md)을 구현해 셜리 대사 두 페이지를 삽입했다. [검증본 003](build/dialogue_paged_003/TinyToon_dialogue_paged.nes)은 2/22블록이며 재빌드/IPS 적용·실제 게임 표시·28프레임 회귀 검사를 통과했다. 아래 2026-10-01 기록도 이전 단계다.

작업 규칙은 [AGENTS.md](AGENTS.md), 재개 지점은 [최신 handoff](docs/HANDOFF.md), 조사 현황은 [SURVEY.md](docs/SURVEY.md)를 확인한다.

타이틀·인게임 자막의 구현 순서와 다른 AI에게 전달할 지침은 [한글화 작업 계획서](docs/LOCALIZATION_WORK_PLAN.md)에 정리했다.

2026-10-01: [게임명 로고 PoC](docs/POC_TITLE.md)를 보존하며 지정 Galmuri7으로 [첫 인게임 대사 삽입 PoC](docs/POC_DIALOGUE.md)를 완료했다. 최신 대사 시험본은 `build/dialogue_kr_poc_004/`, 현재 1/22블록이다. 사용자 번역은 [작업 원천 CSV](workspace/translation/dialogue_ja.csv)의 문구와 `needs_review` 상태를 보존한다. 나머지 삽입·전체 한글 공급·전 장면 QA는 남아 있다. 재개는 [최신 인계](docs/HANDOFF.md)를 따른다. `PUSH START` 등 영문 유지와 기존 한글 로고 보존은 계속 적용한다.

## 폴더 구성

작업 7: 원본 코드·새 실행 캡처에서 **8×8px 글자 칸 / 16열×7행 / 128×56px 대사 영역**을 확인했다. [폰트 크기 조사](docs/FONT_SIZE_SURVEY.md)에 확장 크기의 적용 조건과 실측 근거를 기록했다. 한글 삽입·가독성 검증은 다음 PoC에서 수행한다.

작업 8 최신: 지정 Galmuri7 PNG를 등록하고 `JP_175A9` 한 블록을 실제 ROM에 삽입했다. [시험본 004](build/dialogue_kr_poc_004/TinyToon_dialogue_kr_poc.nes)·[실제 한글 화면](qa/dialogue/kr_poc_004/frame_0810_4x.png)·[대사 삽입 PoC](docs/POC_DIALOGUE.md)를 따른다. 재빌드/IPS 적용 동일, 13개 샘플 화면에서 대사 밖 픽셀 차이 0. 현재 1/22블록이며 원본·기존 타이틀·번역 CSV는 보존한다.


| 경로 | 용도 |
|---|---|
| original/rom/ | 기준 원본 ROM 보관, 수정 금지 |
| extracted/prg/, extracted/chr/, extracted/text/ | 추후 추출할 프로그램·타일·원문 데이터 |
| workspace/translation/ | 번역 원천과 검토 상태 |
| workspace/fonts/, workspace/graphics/ | 한글 폰트 및 그래픽 편집 원천 |
| workspace/tables/, workspace/asm/ | 문자 대응표, 코드 수정 소스 |
| scripts/ | 분석·추출·빌드·검증 재현 스크립트 |
| tools/ | 로컬 도구; 채택 시 출처·버전·라이선스 기록 |
| config/ | 추후 확정할 프로젝트 설정 |
| manifests/ | 원본과 산출물 식별 정보 |
| docs/ | 조사 기록, 작업 지침, 날짜별 인계 |
| work/ | 재생성 가능한 임시 실험 파일 |
| build/ | 빌드 ID별 수정 ROM 및 빌드 결과 |
| dist/ | 배포용 패치와 적용 안내 |
| backups/ | 필요한 변경 전 백업 |
| qa/reports/, qa/logs/ | 정적·실행 검증 보고서와 로그 |
| qa/screenshots/, qa/saves/, qa/states/ | 화면 증거 및 프로젝트 전용 저장 데이터 |

빈 하위 폴더는 향후 작업 위치만 예약한 것이며, 해당 자료가 추출되거나 검증되었다는 뜻이 아니다.

## 원본 확인

프로젝트 루트에서 PowerShell로 실행한다. Windows PowerShell 5.1 이상, 추가 패키지 없음.

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_source.ps1
~~~

원본 경로를 별도로 지정할 수도 있다.

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_source.ps1 -RomPath 'D:\ROMs\Tiny Toon Adventures (Japan).nes'
~~~

검사 기준은 manifests/source_rom.json의 크기와 SHA-256이다. 원본 무결성 검사는 게임 실행 검증과 별개이다.
