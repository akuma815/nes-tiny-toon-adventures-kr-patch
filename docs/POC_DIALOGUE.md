# Galmuri7 인게임 대사 삽입 PoC — 2026-10-01

**2026-10-04 작업 16 최신:** 기존 배포 폴더와 같은 구성으로 [한글 패치 v1.0 릴리즈](RELEASE_2026-10-04.md)를 작성했다. [정식 ZIP](../dist/TinyToonAdventures_KR_Patch_v1.0_20261004.zip)은 xdelta·Windows 적용 도구·한국어 설명서/릴리즈 글·체크섬·검증 보고서·도구/폰트 라이선스의11파일이며 ROM은 포함하지 않는다. 실제 Windows 적용8검사와 최종ZIP추출후적용이PASS이고 결과는 기존006과바이트단위로같다. 등록22블록의장면출력증거와선택/실제엔딩631표본QA는유지했다. CSV22개`needs_review`와이전빌드/QA/테스트002를보존했다. 전체완주/실기/다른에뮬레이터와최종문구검토를완료로표기하지않는다. 아래항목은이전이력이며오늘인계작업16을따른다.

**작업10 이력:** [세 페이지 검증본](DIALOGUE_THREE.md)은3/22블록이다. 방향키/A 선택과 대기중 한글 유지, 후속 폰트 복귀를 확인했고44프레임 대사창 밖 차이0이다. 아래 첫 PoC와 두 페이지 후속 기록은 이전 이력이다.

**2026-10-04 후속 검증:** [페이지별 폰트 공급 003](DIALOGUE_PAGED.md)이 최신이며 2/22블록이다. 캡처를 늘려 기존 첫 대사 PoC의 780·810프레임에 입 모양 차이를 발견했다. 아래 13개 표본 통과는 당시 범위에서 유효하지만 말하기 구간 전체의 동일성을 뜻하지 않는다. 003은 첫 문구/글리프를 유지하며 출력 시간을 보정했고 28프레임에서 대사창 밖 차이0을 검증했다. 기존 ‘IRQ 폰트 선택’은 NMI의 `$FE8C` 호출 경로로 정정한다. 과거 ROM/보고서는 보존했다.

**셜리의 자기소개 `JP_175A9` 한 블록을 사용자 번역 그대로 넣고 실제 게임에서 확인했다.** 글꼴은 사용자가 지정한 `Galmuri7_8x8.png`, 글자 칸은 8×8px이다. 현재 범위는 22블록 중 1블록이며 전체 번역 삽입·전 장면 QA 완료본이 아니다.

최신 시험 ROM은 [dialogue_kr_poc_004](../build/dialogue_kr_poc_004/TinyToon_dialogue_kr_poc.nes), [원본에 적용하는 시험 IPS](../build/dialogue_kr_poc_004/TinyToon_dialogue_kr_poc.ips)다. 기존 한글 타이틀 004를 함께 보존했다. 이 IPS는 로컬 시험용으로 `build/`에만 두며 배포 패키지는 만들지 않았다.

실제 [원본 크기 화면](../qa/dialogue/kr_poc_004/frame_0810.png), [4배 확대 화면](../qa/dialogue/kr_poc_004/frame_0810_4x.png):

```text
하이~ 셜리 더 룬이야
난 예언자거든
```

## 이번 게이트와 판정

8×8px 한글이 실제 대사 소비 경로에서 표시되고, 대사·폰트 변경이 동료 선택 UI·기존 한글 타이틀·후속 안내와 첫 스테이지에 회귀를 일으키지 않는지를 확인했다.

- 가시성·대표 한 블록 E2E: 통과. 입력 CSV→폰트 픽셀→문자 코드→원래 스크립트 위치→실제 CPU 읽기→PPU 글자 배치→게임 화면이 연결됐다.
- 기존 타이틀 004 기준 13개 같은 프레임을 비교했다. 모든 화면에서 대사 영역 `[32,160)×[32,88)` 밖 픽셀 차이 0. 다음 일본어 안내와 스테이지·리셋 후 타이틀은 화면 전체가 동일했다.
- 한글 156종의 공급 예산·전량 조판·전 게임 장면 검증은 통과 범위에 포함하지 않는다. 이 PoC는 새 코드 14개만 사용한다.

## 글꼴 원천과 문자 코드

[workspace/fonts/galmuri7_8x8/](../workspace/fonts/galmuri7_8x8/)에 지정 PNG의 동일 복사본·같은 계열의 로컬 `Galmuri7.ttf`·출처 명세·OFL·매핑 검사 기록을 보존했다. PNG는 512×1400px, 64열, 첫 글자 U+AC00부터 한글 음절 순서로 배열된 8×8px 시트다. 번역 수요 한글 156종을 TTF의 동일 문자와 대조해 전부 픽셀이 대응하는 것을 확인했다. 이 대조는 문자 순서 확인용이며 **한글 픽셀은 PNG에서 직접 추출**한다.

PNG에 없는 `~`만 같은 폴더의 Galmuri7.ttf에서 네이티브 8px로 가져왔다. 공백은 기존 0번 빈 타일을 그대로 사용했다. 폰트 출처·버전·해시는 [font_source.json](../workspace/fonts/galmuri7_8x8/font_source.json), 사용 조건은 원작자 [OFL](https://raw.githubusercontent.com/quiple/galmuri/main/ofl.md)을 기록했다.

- PNG SHA-256: `a2be473e22a62942164c95db60f3f5aa88a99f76b525994d194e9f5f9df387ea`.
- 기호용 TTF SHA-256: `3882bd35066c26b0392cd4963ff9b3c151041dec34adc9d5633d137d1d9b9855`.
- 선택한 새 코드: `$6E–$7B` 14개. 확인된 원문 문자 97개와 겹치지 않으며, 폰트가 활성인 원본 캡처 6개의 두 네임테이블에서 대사 영역 밖 참조가 없었다. [슬롯 소비 조사](../work/dialogue_poc_20261001/slot_consumers.json)를 보관했다. 전체 게임 상태에서 미사용이라는 판정은 아니다.
- 원본 문자의 비트맵·동료 선택 그래픽은 복제 뱅크에서도 그대로 보존한다. 변환은 원본 흰색 문자와 같은 PPU 픽셀 값 2, 2bpp 상위 비트면을 쓴다.

## 삽입 방식과 Expected Write

원본에서 기존 title 004의 Expected Write를 재검증·합성한 뒤 아래 변경을 함께 검증해 새 ROM으로 쓴다. 원본·기존 검증 빌드를 수정하지 않는다.

1. CHR 상대 `0x1E000`(뱅크 120) 및 `0x1A800`(뱅크 106)을 각각 1KiB 복제해 파일 `0x40010`에 새 CHR 뱅크 128·129로 추가한다. 한글 13종과 `~` 하나를 새 코드 위치에 넣고 나머지 6KiB는 명시적으로 0으로 채운다. 기존 CHR는 타이틀 004와 전체 바이트 동일하다.
2. iNES 헤더의 CHR 크기만 16→17(8KiB 단위)로 변경한다. PRG 크기·매퍼·다른 헤더 바이트는 보존한다. VRC4 CHR 레지스터 구조는 [NESdev](https://www.nesdev.org/wiki/INES_Mapper_023)를 참고했으며, 새 뱅크 도달은 Mesen에서 직접 확인했다.
3. CPU `$FE90–$FEA3` / 파일 `[0x1FEA0,0x1FEB4)`의 기존 IRQ 문자 뱅크 선택 명령에서 즉시값 4개만 바꾼다. `$B000/$B004`, `$B008/$B00C`가 새 뱅크 128·129를 선택한다. 명령 경계·분기·레지스터 효과를 바꾸거나 새 코드·훅을 할당하지 않는다. 기존 명령 8개는 py65 1.2.0의 NMOS 6502 디스어셈블러로 검산했다.
4. `JP_175A9` 파일 `[0x175A9,0x175CE)` 37바이트 안에서만 번역한다. 시작·호출·포인터·후속 주소는 그대로다. 원래 속도 `F8 03`, 좌표 `F6 04 04`, 줄바꿈, 대기 `F7 46`을 유지한다.
5. 한국어의 실제 출력 글자가 줄어드는 만큼 48프레임의 추가 대기 `F7 2F`를 넣는다. 원래 `F7 46` 뒤에 붙이며 다음 페이지 `F9` 소비 프레임을 원본과 같은 882로 맞춘다. 남는 8바이트는 동일 속도 설정 `F8 03` 4회로 채워 후속 주소를 유지한다. 표시 공백이나 문자로 패딩하지 않는다.

[전체 쓰기 계획](../build/dialogue_kr_poc_004/expected_writes.json), [문자·타일 대응](../build/dialogue_kr_poc_004/glyph_mapping.json), [빌드 보고서](../build/dialogue_kr_poc_004/build_report.json)를 보관한다. 다른 원본·폰트·CSV, 겹치는 쓰기, 등록되지 않은 diff, 인코딩 누락은 빌드 실패다.

## 시행착오와 현재 채택본

- `dialogue_kr_poc_001`: 원본 문자 팔레트 값과 다른 비트면을 쓴 초기 정적 후보. 실행하지 않았고 채택하지 않는다.
- `dialogue_kr_poc_002`: 한글은 표시됐으나 `$3C–$48` 일부가 동료 선택 UI에서도 소비되어 그래픽이 바뀌었다. 채택하지 않는다.
- `dialogue_kr_poc_003`: `$6E–$7B`로 UI 충돌을 해결했으나, 짧아진 문장으로 다음 안내가 48프레임 일찍 시작돼 셜리 말하는 애니메이션의 프레임이 달라졌다. 채택하지 않는다.
- **`dialogue_kr_poc_004`**: 원본 페이지 전환 시간을 보정한 현재 검증본. 이전 후보·QA는 조사 이력으로 보존한다.

## 검증과 재현

- 정적 / 빌드: Expected Write·헤더·보호 범위·문자 왕복 PASS. 지정 PNG의 한글 156종 문자 순서 대조 PASS. [독립 정적 보고서](../qa/reports/dialogue_kr_poc_004_static.json).
- 재빌드 / 패치 적용: 작업 폰트 복사본으로 별도 재빌드가 바이트 동일. 원본에 실제 IPS CLI 적용한 [출력](../qa/apply/dialogue_kr_poc_004/TinyToon_dialogue_kr_poc_applied.nes)이 빌드와 바이트 동일.
- 에뮬레이터: 원본, title 기준선, 후보 002·003·004를 각각 콜드 부팅했다. 최신 004 종료 0. 컨트롤러 Start/A와 리셋만 사용, RAM/ROM 쓰기·저장 상태 없음. 실제 소비 116건 대조, 첫 블록 37바이트 전부 소비. 다른 대사 읽기 값과 프레임 모두 기준선 동일. PPU가 CHR 뱅크 128·129 및 빌드 폰트 바이트를 실제로 사용했고 한글 네임테이블 배치가 역문과 일치했다. [실행 검사](../qa/reports/dialogue_kr_poc_004_runtime.json).
- 실제 장면 시각: 한글 자기소개 810, 다음 일본어 안내 960, 첫 스테이지 2700, 리셋 후 한글 타이틀 3300을 직접 확인했다. 셜리 대사의 8×8px 가독성은 확인했지만 다른 대사의 겹받침·전체 문자 가독성은 미검증.
- 전체 22블록 삽입 / 나머지 화자·레벨·엔딩 / 전체 플레이 / 배포 검증: 미수행. CSV의 22개 `needs_review` 상태는 그대로다.

최신 ROM SHA-256: `2ea18504ce157ad16ab21dba70986f6cad1872346e9122d597af6aef690bebf2`, 270352바이트.

프로젝트 루트에서 Python 3.12.10 / Pillow 12.3.0 / py65 1.2.0 / Mesen 2.1.1을 사용한다. fontTools는 font source 등록 시 문자 대응 확인에 사용했다. 기존 출력 보호를 위해 새 경로를 지정한다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_source.ps1
# py65가 없을 때만: python -m pip install --target tools/python/py65-1.2.0 py65==1.2.0
python .\scripts\build_dialogue_poc.py --font-png .\workspace\fonts\galmuri7_8x8\Galmuri7_8x8.png --symbol-font .\workspace\fonts\galmuri7_8x8\Galmuri7.ttf --output .\build\dialogue_kr_repro_next
python .\scripts\run_dialogue_poc_qa.py --rom .\build\title_kr_ai_004\TinyToon_title_kr_poc.nes --output .\qa\dialogue\poc_title_baseline_next
python .\scripts\run_dialogue_poc_qa.py --rom .\build\dialogue_kr_repro_next\TinyToon_dialogue_kr_poc.nes --output .\qa\dialogue\kr_poc_next
python .\scripts\verify_dialogue_poc_qa.py --build .\build\dialogue_kr_repro_next --baseline .\qa\dialogue\poc_title_baseline_next --runtime .\qa\dialogue\kr_poc_next --output .\qa\reports\dialogue_kr_runtime_next.json
```

다음은 14개 새 코드로는 수용할 수 없는 전체 156종과 항목별 최대 34종을 위해 페이지별 폰트 공급·코드 선택 및 대사 재배치 설계를 구현하는 것이다. 이번 PoC의 미사용 코드 판정을 다른 장면이나 전체 공급 상한으로 확대하지 않는다. 사용자 번역 문구는 그대로 보존하고 명시 조판을 별도 자산으로 관리한다.
