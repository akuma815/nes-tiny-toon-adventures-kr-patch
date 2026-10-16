# 캐릭터 선택과 실제 엔딩 장면 QA — 2026-10-04 작업 15

**2026-10-04 작업17 최신:** 당근30개 교환 후 공통 작별 대사의 대기 중 폰트가 먼저 바뀌는 오류를 재현·수정했다. ‘몇’의 획도 분리했다. [원인·검증·재현](HAMTON_FONT_FIX_2026-10-04.md), [v1.0.1 ZIP](../dist/TinyToonAdventures_KR_Patch_v1.0.1_20261004.zip)을 따른다. 이전006/작업16 검증은 이 대기 구간의 오류를 놓쳤으며 아래 기록은 이력이다.


사용자 요청에 따라 대사 검증을 위해 플랫폼 스테이지를 계속 플레이하는 절차를 종료했다. **6개 스테이지의 캐릭터 선택과 실제 엔딩으로 바로 이동해 대사를 검증했다.** [자동 검사](../qa/reports/dialogue_full_006_scene_skip.json)는 7개 장면 클래스·고유 11블록·631개 비교 화면 표본에서 PASS다. [직접 시각 검사](../qa/reports/dialogue_full_006_scene_skip_visual.json)도 PASS다.

최신 ROM은 [dialogue_full_006](../build/dialogue_full_006/TinyToon_dialogue_full.nes) 그대로다. SHA-256은 `6d834cdde925dd808ef6d911ebf2f13f5a88e440c9da4bfc50b424035309483d`다. 이번에 ROM/IPS/CSV/폰트를 수정하지 않았다. 기존 [테스트 ZIP002](../dist/dialogue_test_002.zip)은 같은 ROM을 만든다. ZIP의 안내/보고서는 작업14 시점의 검증 범위이며, 추가 장면 검증은 이 문서와 작업15 보고서를 따른다.

## 장면 이동 방식

콜드 부팅 후 원래 장면 디스패처 `$D57C`가 셜리 장면을 호출하기 직전인 664프레임에, 원본과 패치본에 동일한 RAM 변경을 적용했다. [러너](../scripts/run_dialogue_scene_skip.py)는 변경 전후 값과 사유를 각 폴더의 `scene_skip.csv`에 기록한다.

| 장면 | RAM 변경 | 이후 실행 |
|---|---|---|
| STAGE 1~6 선택 | `$53`만 각각 0/5/10/15/20/21로 설정 | 원래 셜리 초기화·레벨별 루트6~11·추천 대사·컨트롤러 선택·루트19 작별·스테이지 진입 |
| 실제 엔딩 | `$53=23`, `$4C=16`, `$05BA=0`, `$05BB=0` | 원래 엔딩 초기화·전용 그림/창 로드·루트22~25·자동 문단 전환·스태프롤 |

저장 상태·ROM 쓰기·CPU PC/A 대체·텍스트 포인터 대체·이미지 복사 없이 원래 게임 코드가 장면을 만든다. **보스를 이겨 엔딩에 도달한 정상 완주 검사로 기록하지 않는다.** 이전 `full_cinema_ending_006`은 도입부 그림 위에 엔딩 문구를 호출한 출력기 검사였다. 이번 검사는 실제 엔딩 전용 초기화와 그림을 사용한다.

각 `qa/dialogue/full_scene_{stage1..stage6|ending}_skip_001/`과 `..._skip_baseline_001/`에는 실행 명령/ROM·에뮬레이터·캡처 스크립트/산출물 해시를 담은 `environment.json`, 선언한 RAM 변경, 매 프레임 컨트롤러 입력, 초기화/F7/FA 이벤트, 실제 스크립트 읽기, 폰트 호출, PRG RAM 접근, PNG/PPU/RAM 캡처가 있다. 비교 원본은 일본어 대사가 남은 타이틀004 ROM이다. Mesen 실행은 설정 파일을 공유하므로 순차 실행한다.

## 검증 결과

- 정적/빌드/패치 적용: ROM 바이트 변경 없이 작업12의 정적·ABI·재빌드·IPS 적용 PASS와 작업14의 실제 Windows 적용 PASS를 유지했다. 최신 ROM·원본·CSV·폰트·봉인 ZIP의 해시는 최종 보존 감사에서 다시 확인한다.
- 에뮬레이터 실행: 6개 선택 화면과 실제 엔딩을 각각 원본/패치본으로 실행, 총14회 모두 종료0. 같은 선언 RAM 변경·컨트롤러 입력·초기화 루트·FA 종료·장면 전환 시간·표본 플레이어/HUD 상태를 확인했다.
- 한글 내용/폰트: 선택 공통4블록·추천3블록·실제 엔딩4블록의 전체 페이지 소비, 완성된 글자 코드, 실제 PPU 폰트 바이트와 페이지별 CHR 선택, 폰트 호출 스택 복원을 확인했다. STAGE2는 플러키 덕, STAGE3은 디지 데블, STAGE4는 퍼볼 추천이 출력된다. STAGE1/5/6에는 별도 추천 문단이 없다.
- 화면 회귀: 같은 시각의631개 캡처에서 텍스트 셀 외 픽셀 차이0. 선택 창의16×7셀은 `(32,32)..(160,88)`, 엔딩은 `(64,144)..(192,200)`다. 그림·테두리·선택 카드·게임 화면·스태프롤을 보호한 비교다. 엔딩 마지막 문단의 중간 대기 시각 차이 때문에 양쪽에만 있는 추가 캡처는 동시각 픽셀 비교에 포함하지 않았다.
- 시간: 첫3개 엔딩 문단의 모든F7 시간과4문단의FA/전환 시간이 원본과 같다. 마지막 `JP_1780B`의F714 중간8회는 기존 삽입 설계대로 번역 위치에 맞춰 재분배되어 내부 시각은 다르지만, 횟수·첫/최종 대기·문단 종료 시간은 같다.
- RAM: 위 실행들에서 원본의PRG RAM 접근0. 패치 접근은 `$6000..6003` 캐시와 승인 도우미/래스터 코드만 사용했다. 전 게임의 RAM 소유권을 전수 조사한 결과로 확대하지 않는다.
- 직접 시각 검사: [선택 화면 모음](../qa/dialogue/full_scene_stage_selection_contact_sheet_001.png)과 [실제 엔딩 모음](../qa/dialogue/full_scene_ending_skip_001/ending_contact_sheet.png)의15개 장면을 직접 확인했다. 한글·줄바꿈·원래A 버튼 기호·작별·4문단의 전용 그림·마지막 ‘끝!!’·스태프롤을 확인했으며 관측한 글자 깨짐/창 넘침은 없다. 자동 타일/픽셀 검사와 분리해 기록했다.

정상 도입부6블록(작업12), [햄튼5블록](DIALOGUE_HAMTON.md)(정상30개와 별도29개 분기), 이번 선택7블록/엔딩4블록을 합치면 **등록22블록 모두 대응 장면 맥락에서 출력 증거가 있다.** 추천과 엔딩의 도달 방법은 위의 선언 RAM 스킵이다. 전체 완주를 이번 대사 표시 검사의 필수 조건으로 추가하지 않는다.

## 이전 플랫폼 탐색의 보존과 정정

`native_walk_023..048.json` 및 해당 실행/캡처를 보존했다. 040은 사용자 설명대로 엘마이라를 피하고 나타난 문으로 들어가 실제 STAGE 1-2 CLEAR와 STAGE 1-3 성 진입을 확인했다. [원본 대조189표본](../qa/reports/dialogue_full_006_native_elmyra_exit.json), [직접 시각 보고서](../qa/reports/dialogue_full_006_elmyra_visual.json), [장면 모음](../qa/dialogue/full_native_walk_040/elmyra_exit_contact_sheet.png)을 따른다.

033의 회귀 검사 자체는 유효하지만, 당시 보고서의 ‘STAGE 1-2 클리어’ 해석은 잘못이었다. 033은 엘마이라 방에 들어간 뒤 붙잡혀 선택 화면으로 돌아왔다. 기존 보고서를 수정/삭제하지 않고 [정정 보고서](../qa/reports/dialogue_full_006_native_stage1_clear_correction.json)를 추가했다. 041~048의 성 탐색은 성공 검증으로 승격하지 않으며 사용자 요청 이후 더 진행하지 않는다.

## 재현

프로젝트 루트, Python3.12/Pillow/프로젝트 py651.2.0/Mesen2.1.1 및 기존 빌드006/타이틀004가 필요하다. 아래 새 출력명으로 순차 실행한다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_source.ps1
foreach ($case in @('stage1','stage2','stage3','stage4','stage5','stage6','ending')) {
  python .\scripts\run_dialogue_scene_skip.py --rom .\build\dialogue_full_006\TinyToon_dialogue_full.nes --case $case --output "qa/dialogue/full_scene_${case}_skip_next"
  if ($LASTEXITCODE -ne 0) { throw 'target capture failed' }
  python .\scripts\run_dialogue_scene_skip.py --rom .\build\title_kr_ai_004\TinyToon_title_kr_poc.nes --source --case $case --output "qa/dialogue/full_scene_${case}_skip_baseline_next"
  if ($LASTEXITCODE -ne 0) { throw 'baseline capture failed' }
}
python .\scripts\verify_dialogue_scene_skip.py --suffix next --output .\qa\reports\dialogue_full_006_scene_skip_next.json
```

[검증기](../scripts/verify_dialogue_scene_skip.py)의 기본 입력은 보존한001이며 출력은 기존 보고서를 덮어쓰지 않는다. 위 명령은 새 캡처 접미사/보고서 출력명을 `next`로 지정한다. 시각 검토는 새 캡처에 별도로 수행한다. 캡처 성공만으로 자동 QA PASS를 뜻하지 않는다.

## 남은 범위와 다음 작업 하나

요청한 대사 출력 QA는 완료했다. CSV22개`needs_review`는 유지했고 최종 번역 검토, 실기/다른 에뮬레이터, 전체 완주/전 게임 RAM 조사 및 최종 공개 릴리스는 별도 범위다. **다음 작업 하나는 CSV22행의 번역 문구와 화자 표기를 최종 검토하는 것이다.** 기존 테스트 묶음은 원본에 적용할 수 있으며 추가 플레이 진행을 이 검토의 선행 조건으로 두지 않는다.
