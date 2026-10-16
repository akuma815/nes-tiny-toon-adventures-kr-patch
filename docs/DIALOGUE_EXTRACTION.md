# 일본어 대사 추출 — 2026-10-01

**2026-10-04 작업 16 최신:** 기존 배포 폴더와 같은 구성으로 [한글 패치 v1.0 릴리즈](RELEASE_2026-10-04.md)를 작성했다. [정식 ZIP](../dist/TinyToonAdventures_KR_Patch_v1.0_20261004.zip)은 xdelta·Windows 적용 도구·한국어 설명서/릴리즈 글·체크섬·검증 보고서·도구/폰트 라이선스의11파일이며 ROM은 포함하지 않는다. 실제 Windows 적용8검사와 최종ZIP추출후적용이PASS이고 결과는 기존006과바이트단위로같다. 등록22블록의장면출력증거와선택/실제엔딩631표본QA는유지했다. CSV22개`needs_review`와이전빌드/QA/테스트002를보존했다. 전체완주/실기/다른에뮬레이터와최종문구검토를완료로표기하지않는다. 아래항목은이전이력이며오늘인계작업16을따른다.

**작업10 이력:** [세 번째 조작 안내](DIALOGUE_THREE.md)를 넣어3/22블록이다. 사용자 문구·버튼 원본 타일·검토 상태를 유지했고 다음은 `JP_1760C`이다. 세 번째 페이지의 실행F3는 슬롯 안에서1바이트 앞당겼으며 원본 포인터/호출자 복귀값은 유지했다. 오늘 인계 작업10을 따른다.

**2026-10-04 최신:** CSV 문구/보호 필드/22개 `needs_review`를 보존하며 [셜리 두 페이지](DIALOGUE_PAGED.md)를 실제 ROM에 삽입했다. 현재 2/22블록이며 다음은 `JP_175EE`이다. 전체 공급·나머지 삽입·전 게임 QA는 남아 있다. 최신 재개 상태는 [오늘 인계](HANDOFF_2026-10-04.md)를 따른다.

번역 작업 파일은 [dialogue_ja.csv](../workspace/translation/dialogue_ja.csv)이다. Excel에서 일본어·한국어를 읽을 수 있도록 UTF-8 BOM으로 저장했다. 셀 안의 줄바꿈은 따옴표로 감싼 정상 CSV 필드다.

**작업 6 현재 상태:** [사용자 번역 제출본](../workspace/translation/dialogue_ja_translated_ko.csv)의 22개 역문을 작업 원천에 문구 그대로 반영했다. 원본 보호 필드는 모두 동일하다. 상태는 `needs_review`이며 한글 표시·재삽입·최종 언어 검수는 아직 남아 있다. [수령 검사](../qa/reports/translation_received_2026-10-01.json), [반영 후 검사](../qa/reports/translation_import_2026-10-01.json) 참조.

확인한 일본어 대사 소비자의 **26개 포인터 슬롯 / 고유 진입점 21개 / 공통 호출 포함 고유 대사·내레이션 22블록**을 전수 추출했다. 처음부터 모든 장면을 플레이한 결과는 아니다. 다른 일본어 표시 경로가 전혀 없다는 전 게임 화면 검증은 아직 수행하지 않았다. 영문 스태프롤·UI는 사용자 확정에 따라 번역 대상에서 제외한다.

## CSV 사용

- `original_jp`: 일본어 읽기용 원문. 탁점·반탁점을 NFC로 결합했다. 별도로 삽입된 대기 시간은 이 칸에 보이지 않는다.
- `translation_ko`, `status`, `notes`: 번역 입력·검토용. 작업 5의 초기 추출은 빈 역문 / `untranslated`였다. 작업 6 현재는 사용자 역문 / `needs_review` 22행이다.
- `speaker`, `speaker_en`, `speaker_status`, `addressee`, `scene`: 화자와 대화 관계. 한국어 이름은 작업용 표기이며 공식 한국어 더빙명으로 인증한 것은 아니다.
- `speaker_basis`, `source_urls`: 판정 근거와 외부 출처.
- `entry_id`, `script_ids`, `file_offset`, `end_exclusive`, `source_tokens`, `raw_hex`, `source_sha256`: 원본 보호 필드. 번역 과정에서 수정하지 않는다.

`script_ids`는 포인터 번호다. 동일 대사를 사용하는 장면 번호를 합쳐 표시했으며 화면 순번·레벨 번호와 같다고 가정하지 않는다. 대사 언급 인물을 화자로 오인하지 않도록 화자와 상대를 별도로 두었다.

`source_tokens`는 각 글자도 `{tile:XX}`로 기록하는 가역 표현이다. 원문을 NFC 문자열에서 다시 인코딩하면 같은 모양의 다른 슬롯을 구분하지 못할 수 있으므로 토큰·원본 바이트를 기준으로 한다. 원문 `デイジーデビル`, `ファーボール`, `バブス` 등의 게임 표기를 임의로 고치지 않았다. `〈A〉`는 6C/6B/6D 방향 기호·A 타일의 읽기용 표기다.

CSV의 한 행은 연속 대사 블록이다. 햄튼의 인사와 보상 설명, 셜리의 자기소개·선택·조작 안내는 창 지우기 명령에 따라 나뉜다. 같은 페이지 안의 `F5` 줄 이동은 실제 줄바꿈으로 남겼다. 도입과 엔딩에는 내레이션도 포함한다.

## 화자와 원작 설정

판정 우선순위는 원문 자기소개·장면 연결 → 실제 게임 그림 → 공식 자료다. 성격이나 문체만으로 화자를 확정하지 않았다.

| 화자 | 블록 수 | 판정 | 관계와 근거 |
|---|---:|---|---|
| 햄튼 J. 피그 | 5 | 자기소개로 확인 | 당근을 가져온 버스터 일행에게 잔기 보상을 안내 |
| 셜리 더 룬 | 7 | 자기소개·실제 화면으로 확인 | 예언자/점술가로서 버스터에게 동료 선택과 구역 조언 |
| 몬태나 맥스 | 2 | 문맥상 유력 | TV에 등장한 납치범이 버스터를 조롱 |
| 밥스 버니 | 1 | 문맥상 유력 | 납치된 밥스가 버스터에게 구조 요청 |
| 버스터 버니 | 1 | 문맥상 유력 | TV를 보던 주인공이 밥스를 구하기로 결심 |
| 내레이션 | 6 | 인물 미지정 | 사건·결말 설명. 버스터나 밥스의 목소리로 단정하지 않음 |

원작은 1990–1992년 **Tiny Toon Adventures**다. 제작사 [Amblin의 원작 소개](https://amblin.com/tv/tiny-toon-adventures/)는 중심 인물과 학교 배경을 확인해 준다. [원작 극장용 장편 소개](https://amblin.com/tv/tiny-toon-adventures-how-i-spent-my-vacation/)도 밥스·버스터의 함께하는 모험과 플러키·햄튼의 관계를 보여 준다. 함께하는 동료 관계를 기준으로 읽고, 원문에 없는 가족 호칭이나 연애 표현은 추가하지 않는다.

[Konami 공식 NES 설명서 스캔](https://www.thegameisafootarcade.com/wp-content/uploads/2017/03/Tiny-Toon-Adventures-Game-Manual.pdf)은 이 게임의 납치범·피랍자·구조자, 셜리의 점술, 햄튼의 당근 보상 역할을 교차 확인하는 근거다. 원작 캐릭터 설명을 포함한 당시 정식 게임 자료이며 제작사 웹사이트 자체의 호스팅은 아니다. [텍스트 전사본](https://www.world-of-nintendo.com/manuals/nes/tiny_toon_adventures.shtml)은 검색 보조용이다.

2023년 **Tiny Toons Looniversity**는 별도 리부트다. [WBD 공식 소개](https://press.wbd.com/us/media-release/cartoon-network-9/tiny-toons-looniversity-voice-cast-revealed)는 밥스·버스터를 쌍둥이로 설정한다. 이 설정을 1991년 NES 게임에 소급하지 않는다. 원작의 관계를 고려하더라도 화자 이름을 지정하는 제어코드가 발견되지 않았으므로 몬태나·밥스·버스터는 CSV에서 ‘유력’으로 유지한다.

## 저장 구조와 제어

- 포인터 테이블: 파일 `[0x17443,0x17477)`, CPU `$B433`, 26개 little-endian 16비트 주소.
- 원문 스크립트: 파일 `[0x17477,0x17845)`, 974 bytes. 모든 루트 및 공통 호출을 따라가면 이 범위를 빈틈 없이 소유한다. 마지막 `FA` 다음부터 프로그램 코드가 시작한다.
- 이 관측 PRG 뱅크의 주소 관계: `file_offset = cpu_address + 0xC010`. 다른 뱅크에 전역 적용하지 않는다.
- 초기화 `$B20E`: A를 두 배로 하여 `$B433/$B434`에서 포인터를 읽고 `$BF/$C0`에 저장.
- 읽기 `$B271`, 실제 `LDA ($BF),Y` 소비 `$B274`, 읽기 콜백의 PC `$B276`에서 원문 읽기를 확인.
- 문자 슬롯은 실행 중 PPU `$0000–$03FF`의 CHR 상대 `$1E000`, `$0400–$07FF`의 CHR 상대 `$1A800`과 대응한다. 폰트 주변 캐릭터·UI 타일은 별도 자산이다.

| 코드 | 인자 | 소비 의미 | 현재 편집 정책 |
|---|---|---|---|
| F3 | 없음 | F4 호출에서 복귀 | 보존 |
| F4 | 16비트 CPU 주소 | 공통 스크립트 호출 | 보존, 향후 재배치 시 재계산 |
| F5 | 없음 | 다음 행으로 이동 | 추출 단계에서는 보존. 번역 조판 이동 허용은 아직 미확정 |
| F6 | 열·행 2바이트 | 문자 시작 좌표 | 보존 |
| F7 | 1바이트 | 대기 카운터 | 보존 |
| F8 | 1바이트 | 문자 간 대기 값 | 보존 |
| F9 | 없음 | 7회 행 지우기 및 좌표 초기화 | 보존 |
| FA | 없음 | 텍스트 활성 상태 종료 | 보존 |
| FB–FF | 없음 | 별도 그림 명령 디스패치 | 이 일본어 본문 영역에는 없음. 범위 밖 의미는 미확정 |

탁점 `33`과 반탁점 `34`도 표시 타일이다. 별도 글자 타일을 바로 바꾸는 방식의 한글화는 아직 설계·검증하지 않았다. 선택 화면에는 입력에 따라 원문 안내가 끝나기 전에 다른 스크립트로 바뀌는 경로가 있으므로 ROM 안의 전체 원문과 한 번의 플레이에서 보이는 분량은 다를 수 있다.

## 검증과 재현

정적 검증은 원본 해시, 26개 루트 종료·호출/복귀, 974바이트 무변경 왕복, 22행 보호 필드 및 토큰 왕복을 확인했다. [추출 기준선](../extracted/text/dialogue_20261001/dialogue_tokens.json), [원문 CSV](../extracted/text/dialogue_20261001/dialogue_original.csv), [QA 보고서](../qa/reports/dialogue_extraction_2026-10-01.json)를 함께 보관한다.

별도 폴더 재추출의 원문 CSV·토큰 JSON·추출 보고서는 기준선과 모두 바이트 동일하다. [재현 검사 보고서](../qa/reports/dialogue_reextract_repro_2026-10-01.json)에 기록했다.

Mesen 2.1.1 원본 콜드 부팅의 유효 증거는 [original_trace_002](../qa/dialogue/original_trace_002/)다. 실제 소비 읽기 75건을 원본과 대조했으며 종료 코드 0이다. CPU 간접 인덱스의 페이지 교차 시 생기는 더미 읽기를 제외했다. `original_trace_001`은 그 필터 이전 이력으로만 보존한다. 현재 세션에서 셜리의 [동료 선택 화면](../qa/dialogue/original_trace_002/frame_0960.png)을 직접 확인했다. 도입·햄튼·전 레벨·엔딩 장면 시각 검증은 미수행이다. 이번에는 수정 ROM 빌드·패치 적용·한국어 표시 검증을 하지 않았다.

프로젝트 루트에서 Python 3.12.10으로 재현한다. 추출은 표준 라이브러리만 사용한다. 기존 출력과 번역 CSV를 보호하므로 재추출은 새 출력 폴더를 사용하고 `--initialize-translation`은 생략한다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_source.ps1
python .\scripts\extract_dialogue.py --output .\extracted\text\dialogue_reextract_001
python .\scripts\run_dialogue_trace.py --output .\qa\dialogue\original_trace_repro_001
python .\scripts\verify_dialogue.py
```

읽기용 CSV에 화자 메타데이터를 붙이는 일회성 준비·직렬화 코드는 `work/dialogue_20261001/prepare_speakers.py`, `finalize_csv.mjs`에 보존했다. 편집 후 CSV를 초기화하는 용도로 다시 실행하지 않는다. 재삽입기는 아직 없으며 번역 CSV를 ROM에 넣는 단계는 별도 작업이다.

번역 반영 이후 검증기는 `python scripts/verify_dialogue.py --output qa/reports/dialogue_translation_source_recheck.json`처럼 별도 QA 경로로 실행해 이전 추출 기록을 보존한다. 번역 수령·수요 검사는 `scripts/review_translation.py`를 사용한다.

작업 7에서 현재 문자 칸 8×8px와 16열×7행 영역을 실측했다. [폰트 크기 조사](FONT_SIZE_SURVEY.md)를 다음 삽입 설계의 기준으로 사용한다. 확장 크기의 수용량 계산과 한국어 실제 표시 검증은 구분한다.

작업 8에서 지정 Galmuri7으로 `JP_175A9` 한 블록을 실제 삽입·실행 검증했다. [대사 PoC](POC_DIALOGUE.md)를 따른다. 추출/번역 CSV는 수정하지 않았고 22개 `needs_review` 상태를 보존한다. 22블록 중 1블록 검증이며 전량 삽입 완료를 뜻하지 않는다.
