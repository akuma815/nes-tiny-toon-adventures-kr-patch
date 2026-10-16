# 햄튼 당근 교환 화면 검증 — 2026-10-04 작업 13

**2026-10-04 작업17 최신:** 당근30개 교환 후 공통 작별 대사의 대기 중 폰트가 먼저 바뀌는 오류를 재현·수정했다. ‘몇’의 획도 분리했다. [원인·검증·재현](HAMTON_FONT_FIX_2026-10-04.md), [v1.0.1 ZIP](../dist/TinyToonAdventures_KR_Patch_v1.0.1_20261004.zip)을 따른다. 이전006/작업16 검증은 이 대기 구간의 오류를 놓쳤으며 아래 기록은 이력이다.


[전체 삽입본 006](../build/dialogue_full_006/TinyToon_dialogue_full.nes)의 햄튼 대사 5블록을 실제 방의 출력 경로에서 확인했다. **30개 교환은 정상 플레이, 29개 부족 분기는 카운터를 한 번 바꾼 검사**다. 두 검사를 합쳐 `JP_17477`, `JP_1748C`, `JP_174BD`, `JP_174D9`, `JP_1750C`를 확인했으며, 모든 분기를 정상 플레이로 수집했다는 뜻은 아니다.

## 정상 진행과 별도 분기 검사

- 정상 진행: 콜드 부팅 → 셜리/파트너 선택 → STAGE 1-1 클리어 → STAGE 1-2 진행 → 당근 30개 수집 → 동굴의 흰 문 진입 → 햄튼 대화/교환 → 같은 스테이지 복귀. ROM/RAM 쓰기, CPU 상태 교체, 저장 상태 사용 없이 컨트롤러 입력만 사용했다. 점프 자동화는 읽기 전용 상태 관측으로 컨트롤러 A 입력을 선택한다.
- 부족 분기: 같은 입력 경로의 5800프레임에서 `$07E1` 당근 카운터만 30에서 29로 한 번 변경했다. 방 진입·화자 그림·분기 선택·텍스트 출력·퇴장은 원래 게임 코드다. **HUD의 기존 30 표시는 직접 갱신하지 않았으므로 화면의 HUD와 주입한 카운터는 다를 수 있다.** 실제로 29개를 수집한 정상 진행 증거로 사용하지 않는다.
- 정상 교환에서는 `$07E0` 남은 목숨이 2→3, `$07E1` 당근이 30→0으로 바뀌었다. 부족 분기에서는 당근 29를 유지했다. 원본과 패치본의 플레이어 상태와 HUD 상태는 각각 같다.

햄튼 방은 **`$57=1`**을 사용한다. 도입부 영화도 같은 값이지만, 햄튼의 대사 위치는 열 4/행 4이며 영화의 열 8/행 18과 다르다. 폰트 선택은 실제 BF/커서 위치에 따라 작동했다. 햄튼의 그림과 일본어 자기소개 `やあ ぼくはハムトン`도 CSV의 화자 판정과 일치한다. 원문·번역·검토 상태는 수정하지 않았다.

## 검증과 증거

- [자동 검사 보고서](../qa/reports/dialogue_full_006_hamton.json): 정상 30개 및 별도 29개, 합계 **429개 화면 표본**. 텍스트 영역 `(32,32)..(160,88)`만 제외하고 화자 그림/창/배경/HUD/스테이지를 비교했으며 밖의 차이는 0이다. 같은 컨트롤러 입력, 초기화 ID, F7/FA 시간, 플레이어 및 HUD RAM도 일치한다.
- 5블록의 모든 표시 글자 코드를 PPU 타일맵에서 대조했고, 각 페이지의 전체 바이트가 실제 읽기 경로에서 소비됐는지 확인했다. NMI 폰트 쌍과 실제 패턴 바이트, 호출 전후 스택을 검증했다.
- 원본의 해당 실행 범위 PRG RAM 접근은 0이다. 패치본은 승인한 `$6000..$6003` 캐시와 폰트/래스터 코드에서만 접근했다. 전체 게임에서의 소유권 증명은 아니다.
- [장면 모음](../qa/dialogue/full_native_walk_020/hamton_contact_sheet.png)과 [직접 시각 검사](../qa/reports/dialogue_full_006_hamton_visual.json)를 별도로 기록했다. 부족 분기 표본은 이미지에도 `CONTROLLED29`로 구분했다.
- [정상 실행 환경](../qa/dialogue/full_native_walk_020/environment.json), [정상 원본 비교 환경](../qa/dialogue/full_native_walk_baseline_020/environment.json), [별도 29개 환경](../qa/dialogue/full_hamton_29_controlled_001/environment.json), [29개 원본 비교 환경](../qa/dialogue/full_hamton_29_controlled_baseline_001/environment.json)에 ROM/에뮬레이터/스크립트/캡처 해시와 실제 명령이 있다.

최신 ROM SHA-256은 `6d834cdde925dd808ef6d911ebf2f13f5a88e440c9da4bfc50b424035309483d`이며 이 작업에서는 ROM을 다시 수정하지 않았다. 입력 및 이전 검증본을 보존했고 삭제하지 않았다. 중간 `native_walk_001..022`의 사망·재진입 미관찰·당근 수 조정 실패는 탐색 기록이며 통과한 장면 검사로 승격하지 않았다.

## 재현

프로젝트 루트에서 Python/Pillow/py65와 Mesen 2.1.1을 사용한다. 새 출력 폴더를 지정한다.

```powershell
python .\scripts\run_dialogue_gameplay.py --rom .\build\dialogue_full_006\TinyToon_dialogue_full.nes --plan .\work\dialogue_full_20261004\native_walk_020.json --output .\qa\dialogue\hamton_native_recheck
python .\scripts\run_dialogue_gameplay.py --rom .\build\title_kr_ai_004\TinyToon_title_kr_poc.nes --source --plan .\work\dialogue_full_20261004\native_walk_020.json --output .\qa\dialogue\hamton_native_baseline_recheck
python .\scripts\run_dialogue_gameplay.py --rom .\build\dialogue_full_006\TinyToon_dialogue_full.nes --plan .\work\dialogue_full_20261004\native_walk_019.json --carrots 29 --output .\qa\dialogue\hamton_29_recheck
python .\scripts\run_dialogue_gameplay.py --rom .\build\title_kr_ai_004\TinyToon_title_kr_poc.nes --source --plan .\work\dialogue_full_20261004\native_walk_019.json --carrots 29 --output .\qa\dialogue\hamton_29_baseline_recheck
python .\scripts\verify_dialogue_hamton_qa.py --build .\build\dialogue_full_006 --native .\qa\dialogue\hamton_native_recheck --nativebaseline .\qa\dialogue\hamton_native_baseline_recheck --controlled .\qa\dialogue\hamton_29_recheck --controlledbaseline .\qa\dialogue\hamton_29_baseline_recheck --output .\qa\reports\hamton_recheck.json
```

## 남은 범위

작업13 이후 [작업15 장면 스킵 QA](DIALOGUE_SCENE_QA.md)에서 다른 스테이지의 셜리 힌트3개와 실제 엔딩4문단/스태프롤을 확인했다. 사용자 요청에 따라 스테이지 플레이 반복은 종료했다. CSV22행의 문구/화자 최종 검토가 다음 작업이다. 실기/다른 에뮬레이터·전체 완주·전 게임 RAM 조사는 이번 대사 표시 검증과 별도 범위다.
