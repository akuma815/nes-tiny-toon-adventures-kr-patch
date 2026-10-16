# 최종 릴리즈 재현 — 타이니툰 1

대상은 기존 v1.0.1의 바이트 단위 재현입니다. 신규 번역이나 게임 동작 수정은 없습니다.

```powershell
python -m pip install -r requirements-rebuild.txt
python scripts/rebuild_release.py --rom "D:/owned/original.nes" --font-dir "D:/fonts"
```

Python 3.12, Pillow 12.3.0, py65 1.2.0, fonttools 4.63.0에서 확인했습니다. Git을 새로 복제한 폴더에서 실행합니다. `build/`가 이미 있으면 중단하여 기존 검증본을 덮어쓰지 않습니다. 원본은 파일명 대신 SHA-256과 길이로 확인하며 입력 파일을 변경하지 않습니다. 신규 에뮬레이터 실행은 하지 않습니다.

타이틀은 채택된 NES 타일·배치 데이터를 원본 참조/편집 바이트 명세로 복원합니다. 대사 토큰을 원본에서 다시 추출하고 CSV 22블록·한글 PNG·기호 TTF·명시적 글리프 override·ASM으로 footer003을 빌드합니다. 최종 타이밍 `--active-font-nops 2`를 사용합니다.

`--font-dir`에는 공급된 `Galmuri7_8x8.png`와 `Galmuri7.ttf`가 필요합니다. 이 환경에서는 프로젝트 루트 `Font/`에 두 파일이 있으며 SHA를 확인했습니다. PNG 시트는 사용자 공급 외부 입력으로 명시하며 Git에 없는 파일을 자동 대체하지 않습니다. TTF SHA도 아래 config에서 확인합니다.

`rebuild/config.json`은 사용 소스/명세/번역 원천의 SHA 목록과 원본·결과 SHA를 고정합니다. `rebuild/*.json`의 baseline 명세는 완성 ROM을 저장하지 않고 보유 원본에서 가져올 위치, 반복 바이트와 편집 바이트만 저장합니다. 채택 당시 타이틀/소형 그림의 고정 결과를 재현하는 입력이며 생성형 이미지의 재생성이나 모든 과거 실험의 재실행은 아닙니다. 과거 작업 전체를 편집 가능한 상태로 복원한다는 주장은 하지 않습니다.

최종 산출물은 `build/final_reproduced/` 아래 ROM·IPS·ExpectedWrites·`REBUILD_RESULT.json`입니다. 원본 전체 SHA, 개별 기대 바이트, 쓰기 범위 중첩 없음, 최종 차이/전체 replay 일치와 IPS 실제 적용 결과를 확인합니다. 최종 ROM SHA는 `d57b816fce99d99eb700ebecc3d2397a1d039418ead3b1233d720c712fb2df3d`입니다. 공개 xdelta의 실제 적용 결과도 별도 감사에서 비교합니다.

원본/완성 ROM은 Git 또는 공개 ZIP에 포함하지 않습니다. 과거 `qa/`와 중간 `build/`를 요구하는 분석/검증 스크립트는 역사 자료이며 이 명령의 재현 의존성으로 간주하지 않습니다. 수정 가능한 CSV·ASM·스크립트는 기존 경로로 보존합니다. 모든 역사 QA/캐시/원본 사본은 최종 릴리즈 재현 입력이 아닙니다.

정적·빌드·패치 적용 결과와 실제 플레이 검수는 구분합니다. 이번 작업에서 새 에뮬레이터 실행·직접 장면 검수·완주는 수행하지 않습니다. 기존 문서의 최종 문구 검토/실기 미완료와 사용자 플레이 보고의 범위는 그대로입니다.
