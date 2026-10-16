# 등록 일본어 대사 22블록 한글 삽입 — 2026-10-04 작업 16

**2026-10-04 작업17 최신:** 당근30개 교환 후 공통 작별 대사의 대기 중 폰트가 먼저 바뀌는 오류를 재현·수정했다. ‘몇’의 획도 분리했다. [원인·검증·재현](HAMTON_FONT_FIX_2026-10-04.md), [v1.0.1 ZIP](../dist/TinyToonAdventures_KR_Patch_v1.0.1_20261004.zip)을 따른다. 이전006/작업16 검증은 이 대기 구간의 오류를 놓쳤으며 아래 기록은 이력이다.


최신 검증용 빌드는 [dialogue_full_006](../build/dialogue_full_006/TinyToon_dialogue_full.nes)이다. 사용자 번역 22블록을 지정 Galmuri7 **8×8px**로 삽입했다. 번역 문구·원문 보호 필드·22개 `needs_review`·영문 유지·한글 타이틀004를 보존했다. **등록 대사의 삽입 완료와 전 게임 플레이 검증은 별개다.**

작업15에서 [각 스테이지 선택과 실제 엔딩](DIALOGUE_SCENE_QA.md)을 선언 RAM 스킵으로 확인했다. 7개 장면 클래스·631개 화면 표본에서 대사 밖 차이0이며 직접 시각 검사도PASS다. 실제 엔딩 전용 그림과 스태프롤을 실행했다. 아래 초기 출력기 검사는 과거 범위로 보존한다.

사용자 요청에 따라 작업16에서 [v1.0 릴리즈](RELEASE_2026-10-04.md)와 [정식 배포 ZIP](../dist/TinyToonAdventures_KR_Patch_v1.0_20261004.zip)을 기존 xdelta 배포 형식으로 작성했다. 실제 적용/최종ZIP 적용PASS이며 동일006이다. 기존 IPS 테스트002도 보존한다.

## 산출물과 재현 입력

| 대상 | 경로 / SHA-256 |
|---|---|
| 검증 ROM, 재빌드 및 IPS 적용 결과 | `6d834cdde925dd808ef6d911ebf2f13f5a88e440c9da4bfc50b424035309483d` |
| [실험용 IPS](../build/dialogue_full_006/TinyToon_dialogue_full.ips) | `ff6b10f01a323519780bcc2a3f320de8a7ec4a426df00088fc12fbc496f4826c` |
| 원본 ROM | `73300dc1505564827ef95ba3e2a06c26aa48920e4981195f32b2101c185ef3dd` |
| 작업 CSV | `85aa940ba608ad8e5edd6ed782f106c89f703d18288f923e0298e5b51bc5eafc` |
| 수령 번역 CSV | `e274e97e75db79ea5d05b2e025cc70b7e9258a701bc1c10bea279ecbb4e8eb50` |
| 지정 PNG | `a2be473e22a62942164c95db60f3f5aa88a99f76b525994d194e9f5f9df387ea` |
| 같은 Galmuri7 TTF | `3882bd35066c26b0392cd4963ff9b3c151041dec34adc9d5633d137d1d9b9855` |

원본은 `original/rom/Tiny Toon Adventures (Japan).nes`, 입력은 [작업 CSV](../workspace/translation/dialogue_ja.csv), [등록 폰트](../workspace/fonts/galmuri7_8x8/Galmuri7_8x8.png), [추출 토큰](../extracted/text/dialogue_20261001/dialogue_tokens.json), `build/title_kr_ai_004/`이다. ROM은 524304바이트이며 PRG/CHR 각256KiB다. 이전 검증본/QA/원본/입력은 보존했고 삭제하지 않았다. [Windows 적용을 검증한 테스트 ZIP](../dist/dialogue_test_002.zip)을 추가했다. 최종 번역 검토/전체 플레이 QA는 남아 있다.

## 스크립트와 폰트 공급

- 등록 시작점26개와 호출6개를 새 PRG bank18의 `$A000..$A37C`로 재배치했다. 데이터는893바이트다. 원래 일본어 `[0x17477,0x17845)` 974바이트를 물리적으로 보존했다. 26개 포인터만 승인 범위 안에서 갱신했다.
- PRG bank17 `$8001`에685바이트 영역의 읽기/폰트 도우미를 넣었다. `$8000`에는17이라는 네이티브 뱅크 식별 바이트를 둔다. 원본 고정 bank14/15는 새 고정 bank30/31로 복사한다.
- 원래 읽기 `$B271` 15바이트와 복사한 `$FE8C` 38바이트 안의37바이트 스텁을 사용한다. 원래 읽기 커서/뱅크/스택 계약을 검증했다. `SEI`는IRQ만 막으므로 읽기 동안 `$2000`의NMI 비트를 끄고, 두 PRG뱅크 복원 뒤 원본 `$D1FF`로 `$FF` 그림자 값을 복원한다. 새 읽기 주소는 이 구조로 임시 매핑한다.
- 폰트는 페이지별22쌍, CHR128..171이다. 각 쌍은 원래120/106 폰트의 복사본이다. 새 글자는6E..7F에 우선 할당하고, 필요할 때01..12까지 쓴다. 최대34종 페이지도 수용한다. 숫자3/0, 느낌표, 따옴표, 버튼〈A〉와 UI3C..48은 원래 타일이다.
- **일부 페이지에서는 원래 가나 슬롯을 재사용한다.** `JP_17619`:01..08, `JP_17657`:01..02, `JP_1778C`:01..02, `JP_177BE`:01..10(16개). 그 외 페이지는6E..7F만 쓴다. 이전 단계의 ‘원래97글리프 전부 보존’은 이 전체 공급에 적용되지 않는다. 새 글자로 쓰지 않은 타일과 보호 UI는 바이트 단위로 보존했다.
- 모든 한글은 지정 PNG의 원래8×8 셀에서 추출했고 낮은 비트플레인0/높은 비트플레인잉크로 인코딩했다. PNG에 없는 `~`, 마침표·쉼표·TV 등은 같은 Galmuri7 TTF의8px 흑백 글리프다. 확대/축소나 AI 재작화는 없다.
- 16칸×7줄을 유지한다. `JP_17764`의18자 줄은16칸 안에서 공백 뒤 줄바꿈하여3줄로 배치했다. 번역의 글자/공백/기존 빈 줄을 보존한다.
- 글자 수가 바뀌어도 각 페이지의 총 타이핑 시간이 원본과 같도록 F8을 조절하고 마지막에 속도3을 복원한다. F7의 수와 인수는 전부 유지한다. `JP_1780B`의 중간 F714 여덟 개는 짧아진 ‘끝!!’에 맞춰 새 위치에 분배했다. 내부 대기 시작 프레임은 바뀌며 최종 대기 시작과 전체 길이는 같다.
- 일반 게임의 `$57==0`에서는 임시 뱅크 매핑 전에 반환한다. 원래와 같은12사이클이며 임의의32×32 PRG 매핑/두IRQ상태에서도 레지스터·플래그·스택이 같다. [2048상태 검사](../qa/reports/dialogue_full_006_stage_guard.json)를 통과했고 RAM/CHR/PRG/PPU레지스터 쓰기는0이다. 도입부/영화/햄튼 방은1, 셜리는2다. 모드 값만으로 레이아웃을 확정하지 않는다. 반환된 공통 호출자6개에서는 마지막 조작 안내 폰트를 다음 글자가 나올 때까지 유지한다.

### 영화 장면의 래스터 처리와 RAM

원본 영화 장면은 NMI의폰트 설정 외에 `$FB72..$FBA1` IRQ경로에서 아래 대사창용120/106 폰트를 다시 설정한다. 이 경로에도 페이지 폰트를 공급했다. 가변 길이 선택기를 IRQ에서 실행하면 캐릭터 그림6픽셀이 달라지는 문제가 있었으므로, **네이티브 경로와 같은85 CPU사이클**로 끝나는 캐시 읽기로 바꿨다. 그 결과 검증 표본의 대사창 밖 차이가0이다.

`$6000..$6003` PRG RAM 네 바이트가 패치 폰트 레지스터 캐시다. 헤더 byte8은1로8KiB를 명시한다. 기존 BF/C0/07A9 읽기 커서와 스택 외 내부RAM은 새로 쓰지 않는다. Mesen에서 nesWorkRam 매핑/쓰기·읽기·복원을 확인했다. 원본 도입부와 자동 데모4200프레임의 PRG RAM 접근은0, 새 ROM의 접근은 캐시 네 바이트와 승인 코드뿐이다. ROM바이트를 명령으로 잘못 읽으면 나타나는 `$6000` 주변 후보 참조는 정렬되지 않은 피연산자/그래픽 데이터였다. **전체 게임에서의 RAM 소유권과 실기 동작은 아직 미검증**이다.

## 검증을 구분한 결과

| 구분 | 수행 범위 |
|---|---|
| [정적 / 재빌드 / 실제 IPS 적용](../qa/reports/dialogue_full_006_static.json) | 7개 Expected Write의 원본 해시·비중첩·전체diff 소유권, 22개 문구·폰트 픽셀, 26개 루트·6개 호출·종료 그래프, 복사/이동/패딩, 재빌드와 한국어·공백 포함 프로젝트 경로의 실제 적용 결과 동일 |
| [명령/ABI 모델](../qa/reports/dialogue_full_006_abi.json) | 공식151 opcode/mode와604 인코딩 벡터, 폰트81920 / 읽기21462 / 뱅크교차2240 상태, 스택·두PRG뱅크·IRQ·NMI 마스크 쓰기 순서, 네이티브와 같은85사이클 래스터23쌍 |
| [실제 실행과 픽셀](../qa/reports/dialogue_full_006_runtime.json) | 셜리4블록 정상진행44표본, 무입력 도입부6블록/타이틀/자동데모50표본, 별도 페이지 호출22표본, 26루트 실제 FA 종료, 각 글꼴/PPU타일/읽기값 확인 |
| [영화 출력기 추가 검사](../qa/reports/dialogue_full_006_cinema.json) | 도입부4개의CPU A 시작점만22..25로 교체하여 엔딩4블록을 영화용1모드·래스터 경로로 출력. 36표본. **게임의 실제 엔딩 진입 검사는 아니다.** |
| 직접 시각 검사 | 최신 [22블록](../qa/dialogue/full_harness_006/contact_sheet.png), [정상 도입부](../qa/dialogue/full_attract_008/intro_contact_sheet.png), [엔딩 출력기](../qa/dialogue/full_cinema_ending_006/ending_consumer_contact_sheet.png)의 글자·행·기호를 직접 확인했다. 자동 타일검사와 구분한다. |

위 네 실행 클래스의 **152개 화면 표본**에서 대사창 밖 픽셀 차이는0이다. 이 수는 표본 수이고 전 프레임/전 플레이 검증을 뜻하지 않는다. 강제 페이지 호출은 셜리 화면에서 BF/C0 등 명시된 RAM을 바꿨고, 강제 루트는 네이티브 B20E 초기화의CPU A만 바꿨다. 강제 엔딩 출력은 F7E0의CPU A만 바꿔 **도입부 그림으로 엔딩 문구를 표시**한다. 각 환경 JSON에 조작·ROM/도구/스크립트 해시와 캡처가 있다. 최종 캡처 스크립트 스냅샷도 보존한다.

[햄튼 실제 방](DIALOGUE_HAMTON.md)에서는 정상30개 교환/스테이지 복귀와 별도29개 카운터 분기를 추가 확인했다. 두 클래스429표본에서 텍스트 밖의 화자 그림/배경/HUD 차이는0이며 전체5블록의 글자와 폰트도 확인했다. 이는 위152표본과 별도 집계이고 일부 앞 구간이 겹친다. 29개는 RAM 카운터를 한 번 변경한 검사다. [교환 후 진행192표본](../qa/reports/dialogue_full_006_native_post_hamton.json)도 원본과 같지만 적 충돌/재시작/컨티뉴 대기에 도달했으며 다음 구역 클리어를 뜻하지 않는다.

### 중간 시도 보존

`dialogue_four_001`은 ‘그럼 또 봐’까지4블록과44표본을 확인한 중간본이다. 전체001은 셜리에서는 정상이나 영화 IRQ가 원래 폰트로 되돌아가므로 최신으로 쓰지 않는다. 전체002/003은 영화 대사는 나오지만 가변 IRQ 계산에 따른 캐릭터6픽셀 차이가 남았다. 전체004에서85사이클 캐시로 해결했고, 전체005는 일반 게임의0모드 폰트 변경을 막았다. 전체006에서는 이 검사를 고정 스텁의 맨 앞에 두어 원래와 같은12사이클·무매핑 반환까지 보장한다. 프로브001/002 실패·보조 ABI 검증기의 잘못된 가정과 수정 흔적을 work/QA에 보존했다. 실패를 검증 완료로 승격하지 않았다.

## 재현

프로젝트 루트에서 Python3.12.10/Pillow12.3.0/py65 1.2.0/Mesen2.1.1과 위 입력이 필요하다. 기존 산출물을 덮지 않도록 출력명을 새로 지정한다. 기록된 최종 실행 목록은 [run_final_gates_006.py](../work/dialogue_full_20261004/run_final_gates_006.py), 로그는 [final_gates_006.log](../work/dialogue_full_20261004/final_gates_006.log)에 있다. 해당 스크립트를 같은 이름으로 다시 실행하면 보존 가드가 차단하므로 새 출력명으로 복사한다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_source.ps1
python .\scripts\build_dialogue_full.py --output .\build\dialogue_full_repro_next
python .\scripts\dialogue_ips.py create --source '.\original\rom\Tiny Toon Adventures (Japan).nes' --target .\build\dialogue_full_repro_next\TinyToon_dialogue_full.nes --patch .\build\dialogue_full_repro_next\TinyToon_dialogue_full.ips --scope '22/22 registered dialogue; experimental'
python .\scripts\dialogue_ips.py apply --source '.\original\rom\Tiny Toon Adventures (Japan).nes' --patch .\build\dialogue_full_repro_next\TinyToon_dialogue_full.ips --output .\qa\apply\dialogue_full_repro_next\TinyToon_dialogue_full_applied.nes
python .\scripts\verify_dialogue_full_static.py --build .\build\dialogue_full_006 --rebuild .\build\dialogue_full_repro_next --applied .\qa\apply\dialogue_full_repro_next\TinyToon_dialogue_full_applied.nes --output .\qa\reports\dialogue_full_static_recheck.json
python .\scripts\verify_dialogue_full_abi.py --build .\build\dialogue_full_repro_next --output .\qa\reports\dialogue_full_abi_recheck.json
python .\scripts\run_dialogue_full_qa.py --rom .\build\dialogue_full_repro_next\TinyToon_dialogue_full.nes --scenario cold --output .\qa\dialogue\full_cold_recheck
python .\scripts\run_dialogue_full_qa.py --rom .\build\dialogue_full_repro_next\TinyToon_dialogue_full.nes --scenario attract --output .\qa\dialogue\full_attract_recheck
python .\scripts\run_dialogue_full_harness.py --build .\build\dialogue_full_repro_next --output .\qa\dialogue\full_harness_recheck
python .\scripts\run_dialogue_roots_qa.py --build .\build\dialogue_full_repro_next --output .\qa\dialogue\full_roots_recheck
python .\scripts\run_dialogue_cinema_qa.py --rom .\build\dialogue_full_repro_next\TinyToon_dialogue_full.nes --output .\qa\dialogue\full_cinema_recheck
```

정적/실행 검증기는 `scripts/verify_dialogue_full_static.py`, `verify_dialogue_full_abi.py`, `verify_dialogue_full_qa.py`, `verify_dialogue_cinema_qa.py`다. 실행 검증기 인수의 원본 비교본은 각각 `three_title_baseline_001`, `full_attract_baseline_003`, `full_harness_baseline_002`, `full_roots_baseline_001`, 영화 검증은 `full_cinema_ending_baseline_001`을 사용한다.

## 남은 작업과 다음 한 가지

선택 공통4블록·추천3블록·실제 엔딩4블록은 [작업15 장면 스킵 QA](DIALOGUE_SCENE_QA.md)에서 확인했다. 기존 정상 도입부6블록/햄튼5블록과 합쳐 등록22블록 모두 대응 장면의 출력 증거가 있다. 실기/다른 에뮬레이터, 전체 완주/전 게임 RAM 조사, 번역 검토 및 최종 공개 릴리스는 별도 범위다. 최종 문구/화자 검토 상태는 그대로 유지한 채 사용자 요청으로 [작업16 릴리즈](RELEASE_2026-10-04.md)를 작성했다. **다음 한 가지는 준비한 ZIP과 릴리즈 안내를 사용자가 정한 배포 위치에 게시하는 것이다.** 테스트002는 같은 ROM의 작업14 시점에 봉인한 묶음이며 적용 절차는 [안내 원천](README_DIALOGUE_TEST_KO.md)을 따른다. 추가 QA는 작업15 보고서에 있다.

관련 기술 근거: [Mesen 공식 Lua API](https://github.com/SourMesen/Mesen2/blob/master/UI/Debugger/Documentation/LuaDocumentation.json), [NESdev NMI](https://www.nesdev.org/wiki/NMI), [Mapper023](https://www.nesdev.org/wiki/INES_Mapper_023). API/하드웨어 문서는 구현 근거이며 위 ROM의 실행 증거를 대신하지 않는다.
