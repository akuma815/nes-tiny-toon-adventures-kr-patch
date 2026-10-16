# 타이틀 로고 한글화 PoC — 2026-10-01

사용자의 **원본 PNG 추출 → 생성형 AI로 한글 로고 제작 → NES 타일로 변환 → ROM 재삽입** 방식을 게임명 로고에 적용했다. 현재 검증본은 `build/title_kr_ai_004/TinyToon_title_kr_poc.nes`이다. 전체 게임 한글화나 배포 릴리스가 아니다.

## 산출물과 범위

- [원본 로고 PNG](../extracted/title/title_20261001/logo_original_8x.png)
- [AI 원천 PNG](../workspace/graphics/title/ai_v001/logo_ai_raw.png): 내장 image_gen 도구로 원본 PNG를 편집했다. 결과 자체를 고정 입력으로 보존한다.
- [생성 프롬프트](../workspace/graphics/title/ai_v001/PROMPT.txt)
- [NES용 176×88, 4색 PNG](../build/title_kr_ai_004/logo_nes.png)
- [실제 에뮬레이터 타이틀](../qa/title/kr_smoke_005/frame_0240.png), [4배 확대](../qa/title/kr_smoke_005/title_4x.png)
- [실험 ROM](../build/title_kr_ai_004/TinyToon_title_kr_poc.nes), [실험 IPS](../build/title_kr_ai_004/TinyToon_title_kr_poc.ips), [빌드 보고서](../build/title_kr_ai_004/build_report.json)
- [Expected Write](../build/title_kr_ai_004/expected_writes.json), [원본/수정본 장면 비교](../qa/title/kr_smoke_005/comparison.json)

게임명은 위 줄 ‘타이니 툰’, 아래 줄 ‘어드벤처’로 제작했다. 이번 PNG 실험 범위는 **게임명 로고**이다. 2026-10-01 작업 4에서 사용자는 **영문을 추가 번역하지 않고 원문 유지**, **일본어 번역은 다른 AI와 진행**으로 확정했다. `PUSH START` 한글화 계획은 취소하며 미완료 번역 과제로 집계하지 않는다. 기존 한글 로고와 회사명·저작권은 보존한다. 이 세션은 종료했다.

## 확인된 저장·표시 경로

| 항목 | 확인 결과 |
|---|---|
| 원본 ROM SHA-256 | `73300dc1505564827ef95ba3e2a06c26aa48920e4981195f32b2101c185ef3dd` |
| 검증본 ROM SHA-256 | `beb669edda6c666a10c7b933f5ebee5eecda81ca46d31d17e33d51d6657103b4` |
| AI 원천 PNG SHA-256 | `7bf7615b85650fb784026b71433b655ea8538df24f0a00835e48d61968e4e23b` |
| 배경 CHR | PPU `$0000–$0FFF` → 1KiB 뱅크 56–59 → 파일 `[0x2E010,0x2F010)` |
| 타이틀 배치 | 파일 `[0x3654,0x37FB)`, 423바이트; 런타임 CPU 시작 `$B644` |
| 배치 출력 | PPU `$2000`부터 1024바이트: 타일 번호 960 + 속성표 64 |
| RLE 소비 | CPU `$B595` 부근, 파일 `0x35A5` 부근의 `$2006/$2007` 전송 루틴 |
| 관측된 직접 읽기 | 프레임 6, CPU PC `$B59C/$B5A2/$B5B0/$B5C1/$B5DC`에서 해당 스트림 읽기 |
| 색상 | PPU 팔레트 `0F 20 21 12`: 검정, 흰색, 하늘색, 파랑 |
| 슬롯 예산 | 타이틀에서 확인된 편집 가능 슬롯 158개 / 사용 156개 |
| 압축 예산 | 유효 스트림 408바이트 / 기존 extent 423바이트 |
| 변경량 | 2578바이트, Expected Write 157건 |
| 헤더·ROM 크기 | 원본과 동일, 262160바이트; ASM 훅·뱅크/ROM 확장 없음 |

원본 PPU 메모리와 CHR 페이지를 대조했고 원본 압축 배치의 해제 결과가 런타임 네임테이블과 일치했다. 수정본에서도 동일 뱅크 선택과 새 PNG의 표시를 확인했다. [정적 추출 명세](../extracted/title/title_20261001/title_extraction.json), [실행 중 읽기 트레이스](../qa/title/trace_003/title_rle_reads.csv)에 주소 연결을 기록했다.

RLE는 2바이트 little-endian PPU 목적지로 시작한다. `01–7F`는 다음 값을 반복하고 `81–FF`는 하위 7비트 개수의 리터럴이다. `00`은 종료이다. **`80`은 새 목적지 제어이며 패딩으로 사용할 수 없다.** 현재 빌더는 단일 목적지 구간만 지원하며 원본의 새 목적지 명령은 오류로 거부한다. 재압축 뒤 첫 `00`으로 종료하고 남는 15바이트는 원본 데이터를 그대로 보존한다. 다음 스트림 위치·포인터는 바꾸지 않는다.

원본의 로고 일부 타일 `6C`는 캐릭터 쪽에서도 쓰이므로 변경하지 않는다. 빈 타일 `00`, 캐릭터 조각 `F0/F1`과 로고 우측 하단 `TM` 타일 `CA`도 보호한다. 속성표·팔레트·OAM 데이터는 수정하지 않는다. 풀의 ‘158개’는 현재 타이틀에서 확인한 소비 범위이며 전 게임의 독점 사용을 증명한 수치가 아니다.

## 검증 결과

### 정적·빌드·적용

- 원본 RGB PNG → NES 2bpp 타일 왕복: 원본 타일과 바이트 동일. 무변경 ROM도 원본 SHA-256과 동일.
- 원본에서 Expected Write 전체를 계산·검증하고 적용한다. 허용 범위 밖 diff, 겹치는 쓰기, 타일/압축 예산 초과, 보호 영역 침범은 실패한다.
- 새 압축 해제 결과와 목표 네임테이블 일치, 속성표와 보호 타일 보존.
- 최신 스크립트로 `build/title_kr_ai_004_repro/`에 재빌드해 ROM 해시 동일. 004의 정적 미리보기도 캐릭터 스프라이트 겹침과 TM 보호를 반영하며 실제 타이틀과 픽셀 동일하다. 이전 003과 repro2의 미리보기/마스크는 최신 증거로 사용하지 않는다.
- IPS를 실제 적용 스크립트로 `qa/title/패치 적용 확인 004/TinyToon_applied.nes`에 적용: 위 검증본 해시와 동일. 이 IPS는 시험용이며 `dist/` 릴리스는 만들지 않았다.

### 실행·장면 시각

Mesen 2.1.1 공식 Windows 빌드, 실행 파일 SHA-256 `d2eb03c2590c648bf329f127ebcfefd70130e7690a9e2ccdba8616faea1fe96b`. GUI 화면 조작 대신 headless test runner로 실제 CPU/PPU를 실행해 PNG·PPU·OAM·상태를 저장했다. 저장 상태를 불러오지 않은 콜드 부팅이다.

- 원본/수정본 각각 2100프레임 실행, 종료 코드 0.
- 시작 버튼: 프레임 240–247, 600–607. 프레임 900부터 120프레임마다 A 8프레임. 프레임 1500에 리셋.
- 프레임 120/240/360/1620/1800: 한글 로고 표시. 허용 로고 영역 밖 픽셀 차이 0.
- 프레임 600/900/960/1200/1500/2100: 원본/수정본 PNG 전체 픽셀 동일. 지도, 캐릭터 안내, 첫 스테이지와 리셋 후 대기 전환을 포함한다.
- 240 타이틀, 900 안내, 1200 첫 스테이지, 1620 리셋 타이틀을 직접 시각 확인했다. 한글 원천과 NES 4색 변환본도 확대·원래 화면 크기로 확인했다.
- [원본 실행 환경](../qa/title/original_smoke_004/environment.json), [수정본 실행 환경](../qa/title/kr_smoke_005/environment.json), [비교 모음](../qa/title/kr_smoke_005/comparison_contact.png).

음악의 청취, 두 번째 독립 에뮬레이터, 실기, 장시간 플레이, 엔딩 및 전 게임 공유 타일 조사는 미수행이다. 게임명 디자인과 글자 가독성의 사용자 최종 검수도 아직 받지 않았다.

### 실패 실험과 실행 환경의 함정

`build/title_kr_ai_001`, `002`, `003`과 과거 QA는 이력으로 보존하되 최신 검증본으로 사용하지 않는다. 초기 RLE 패딩 `80`은 잘못된 해석이라 수정했다. `002`의 NES 2.0/서브매퍼 변경 가설도 최종본에는 채택하지 않았다.

초기 최소 Mesen 설정에서는 원본은 CRC 데이터베이스가 컨트롤러를 연결하고 수정본은 CRC가 달라 자동 연결이 되지 않았다. 이 때문에 Start가 적용되지 않는 현상이 있었다. 두 ROM 모두 `config/mesen_title_qa.json`으로 NES 컨트롤러를 명시하면 같은 입력과 게임 진행이 확인된다. 최종 004는 로고 우측 하단의 TM 타일도 보호한다. 최종본은 원본 헤더를 유지한다. DB는 원본을 mapper 23/submapper 2로 식별하지만 수정본은 알려지지 않은 CRC이다. 다른 에뮬레이터의 매퍼 선택은 별도 검증해야 한다.

첫 캡처 스크립트의 `emu.exit`는 2.1.1에서 유효하지 않아 timeout 종료했다. 현재는 소스에서 확인한 `emu.stop(0)`으로 종료하며, 초기 `original_20261001`은 PPU 추출 증거로만 사용한다. `trace_001`은 콜백 주소를 물리 주소로 잘못 표기한 이력이다. 올바른 주소 변환은 `trace_003`를 사용한다.

## 재현

프로젝트 루트, Python 3.12.10 / Pillow 12.3.0. Mesen은 `tools/mesen-2.1.1/Mesen.exe`에 둔다. 출력 폴더는 기존 것을 덮어쓰지 않도록 새 이름을 사용한다. AI 재생성은 동일 결과를 보장하지 않으므로 빌드에는 보존된 PNG를 쓴다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_source.ps1
python .\scripts\extract_title.py
python .\scripts\build_title.py --png .\extracted\title\title_20261001\logo_original.png --output .\build\title_roundtrip_new --roundtrip
python .\scripts\build_title.py --png .\workspace\graphics\title\ai_v001\logo_ai_raw.png --output .\build\title_kr_ai_new
python .\scripts\run_title_qa.py --rom '.\original\rom\Tiny Toon Adventures (Japan).nes' --output .\qa\title\original_new
python .\scripts\run_title_qa.py --rom .\build\title_kr_ai_new\TinyToon_title_kr_poc.nes --output .\qa\title\kr_new
python .\scripts\compare_title_qa.py --original .\qa\title\original_new --patched .\qa\title\kr_new
python .\scripts\title_ips.py apply --source '.\original\rom\Tiny Toon Adventures (Japan).nes' --patch .\build\title_kr_ai_004\TinyToon_title_kr_poc.ips --output .\build\applied_new\TinyToon_applied.nes
```

`run_title_qa.py`가 프로젝트 전용 Mesen의 `settings.json`을 위 QA 설정으로 작성한다. 전역 Mesen 설정은 사용하지 않는다. 원본 스냅샷은 `qa/title/original_20261001`이 필요하며 처음부터 새 환경을 구성할 때에는 동일 스크립트로 프레임 240을 캡처해 이 위치에 제공한다.

## 기술 자료

- [Mesen 2.1.1 공식 배포](https://github.com/SourMesen/Mesen2/releases/tag/2.1.1)
- [공식 Lua API 정의](https://github.com/SourMesen/Mesen2/blob/master/UI/Debugger/Documentation/LuaDocumentation.json), [headless 실행 구현](https://github.com/SourMesen/Mesen2/blob/master/UI/Utilities/TestRunner.cs)
- [Mesen VRC2/VRC4 구현](https://github.com/SourMesen/Mesen2/blob/master/Core/NES/Mappers/Konami/VRC2_4.h), [NESdev 매퍼 사양](https://www.nesdev.org/wiki/INES_Mapper_023)

게임별 주소와 PNG·타일 대응은 로컬 ROM/PPU/트레이스에서 확인했다. 외부 자료는 도구 API와 매퍼 가설 확인에 사용했다.

## 다음 작업 하나

다른 AI가 기준 원본과 기존 타이틀 변경을 확인한 뒤 대표 일본어 대사/안내의 실제 표시 경로를 조사한다. 영문은 원문을 유지한다. 이 세션에서는 후속 작업을 실행하지 않는다.
