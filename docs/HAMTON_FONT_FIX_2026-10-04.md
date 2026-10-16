# 당근 교환 대기 구간 폰트 수정 (작업17)

최신 배포는 [v1.0.1 ZIP](../dist/TinyToonAdventures_KR_Patch_v1.0.1_20261004.zip), 빌드는 [footer003 ROM](../build/dialogue_footer_fix_003/TinyToon_dialogue_full.nes)이다. 기존 배포와 동일한 ROM 없는11파일 구성으로 작성했다. 기존 원본·CSV·폰트PNG·검증산출물·v1.0 ZIP은 보존했다.

## 사용자 사진과 원인

두 번째 사진은 부족 안내가 잘린 것이 아니라, “그럼 몇 개인지 / 세어 볼게”의 화면 글자 코드에 건너뛴 부족 안내 페이지의 폰트가 적용된 상태였다. 기존006 ROM의 [frame6540](../qa/dialogue/full_native_walk_020/frame_06540.png)에서 같은 “.아 쉽 지만당 / 근이 조금”을 재현했다. 글자 코드는 페이지2지만 실제 폰트는134/135(페이지3)였다. [수정 전후 실제 캡처](../qa/dialogue/footer003_visual_001/footer_before_after.png)는 위가006, 아래가수정본이다.

정상30개 교환은 페이지3을 건너뛰고 공통 작별 root18(A078)로 이동한다. 그 시작의 F7 대기 동안 기존 폰트 선택기가 주소상 앞선 페이지3을 선택했다. 부족 분기는 이미 페이지3을 표시하고 있어 이 오류가 드러나지 않았다. 이전 QA는 완성된 문단 하나와 본문 외 픽셀만 확인하여 문단 사이 대기 중의 잘못된 폰트를 놓쳤다.

## 변경

- [빌더](../scripts/build_dialogue_footer_fix.py)는 root18의 cursor<6 구간에서 기존 IRQ 폰트 캐시6000~6003을 읽어 실제 직전 문단의 폰트를 유지한다. 캐시가 초기값이면 원래 폰트로 안전하게 돌아간다. 첫 작별 글자부터 페이지4를 선택한다.
- [명시적 글리프](../workspace/fonts/galmuri7_8x8/glyph_overrides_dialogue_008.json)는 ‘몇’ 한 글자에서 ㅁ·ㅕ와 ㅊ의 획을 분리한다. 지정PNG/TTF는 수정하지 않는다.
- 기존006의 대사 A000~A37C,26root/6call, bank18 읽기, NMI 보호·38바이트 진입부·IRQ85사이클·은행복원·UI 슬롯을 보존한다. 추가RAM은 사용하지 않는다. 대사 문구·공백·줄 배치도 보존한다.
- 새 helper가 실행되는 실제 화면에서 본문 외 픽셀 차이가 없도록 ACTIVE_FONT에2NOP을 둔다. footer001/002의 자연 도입부에서 발견한 본문 외5~6픽셀 차이는 이 후보들을 채택하지 않은 이유다.

## 검증 구분

정적: [독립 정적 검사](../qa/reports/dialogue_footer_003_static.json) PASS. 원본SHA/7 Expected Write 중첩·소유권, 모든 차이,22문단 글리프와 UI 슬롯,26그래프/6호출,974바이트 일본어 원본 보존을 확인했다. [ABI](../qa/reports/dialogue_footer_003_abi.json) PASS: 폰트81920조건·대사읽기21462조건·다른은행2240조건·두직전폰트와기본폰트756조건, IRQ23쌍85사이클 및604 ISA 조건.

빌드/적용: footer003과별도 footer_fix_repro_003 재빌드는 바이트 동일하고 별도 IPS CLI 적용도 동일하다. [배포 적용 보고서](../qa/reports/release_TinyToonAdventures_KR_Patch_v1.0.1_20261004_final.json)는 실제 Windows apply.cmd8검사와 최종ZIP추출본 적용 PASS다. 한글/공백경로, 원본/기존출력보호·잘못된입력/변조패치/도구거부를 포함한다.

실행: [런타임](../qa/reports/dialogue_footer_003_runtime.json) PASS. Mesen2.2.1에서 원래 조작 경로로 수집한30개 교환, 별도$07E1=1 단일RAM쓰기로 부족 분기를 확인했다. 무입력 자연 도입부6문단, 원래 처리기에 명시적RAM스킵으로 진입한6선택·실제엔딩4문단을 확인했다. 공통 1491 캡처에서 본문 외RGB차이0이며 모든22문단의 완전 출력·공백 포함실제픽셀·읽은ROM값·폰트·SP·장면초기화/FA/모드시간을 확인했다. Mesen2.1.1에서도 동일ROM의 두교환분기를 별도로 실행했다. 작별 대기 중 모든 수집프레임은 직전문단의 글자코드 및 모든 잉크/빈픽셀을 검사하고, 지우기부터 다음글자 전까지도 모든폰트호출을 검사한다. 지우기중 프레임끝남테이블과 이미그려진화면의1프레임차이는 완성문단 검사에 혼동하지 않는다.

직접 시각 검토: [보고서](../qa/reports/dialogue_footer_003_visual.json), [당근](../qa/dialogue/footer003_visual_001/hamton.png), [선택](../qa/dialogue/footer003_visual_001/selection.png), [도입](../qa/dialogue/footer003_visual_001/intro.png), [엔딩](../qa/dialogue/footer003_visual_001/ending.png). 별도2.1.1 캡처와 수정전후도 직접 확인했다.

미수행: 전체완주·실기·최종문구/화자검토. CSV22개 needs_review 유지. 정상 실행 경로의 대기 구간 오류를 해결했지만 모든게임RAM에대한캐시소유권 증명이나 모든에뮬레이터 보장을 뜻하지 않는다.

## 보존한 조사와 사용자 실행

007~013 native-reader 실험은 원래읽기복원·타이밍조사를 위한 후보였으며 이번 오류를 해결하지 못해 배포하지 않았다. 해당 중간 QA가 PASS인 경우에도 대기구간검사가 없으므로 최종해결 증거가 아니다. work/hamton_fix_20261004의 native RC 준비 스크립트/문서는 미실행·미배포다. 실제 채택한 수정은006 구조를 유지한다. 사용자 H:/Mesen 실행파일/설정/저장상태는 읽기와 복사만 했으며 변경하지 않았다. 테스트는 격리 복사본에서 수행했다.

새 xdelta를 일본판 원본에 적용해 새 이름의ROM을 처음부터 실행한다. 오류가 발생한 대화 도중의 이전 저장상태는 폰트/화면 상태를 되가져올 수 있으므로 확인에 사용하지 않는다. 대사 주소 변경에 따른 저장상태 비호환을 주장하지 않는다.

## 해시와 재현

| 대상 | SHA-256 |
|---|---|
| 일본판 원본 | `73300dc1505564827ef95ba3e2a06c26aa48920e4981195f32b2101c185ef3dd` |
| footer003 ROM | `d57b816fce99d99eb700ebecc3d2397a1d039418ead3b1233d720c712fb2df3d` |
| IPS | `93b2e5e3d178ea718c2298ddac81add763c5dfaf45d5d765b808d6ee7e8f73e9` |
| v1.0.1 ZIP | `d3bf3ae72fe6567fd5386aa7db2be07d94da1c1092d4ac1c3866cc31f2b4baa7` |
| xdelta | `03d916e0440fdd52fe97c0223dfbac6931ea15a0dd7c36acdd4a10ae00620878` |
| 번역CSV | `85aa940ba608ad8e5edd6ed782f106c89f703d18288f923e0298e5b51bc5eafc` |
| 지정PNG | `a2be473e22a62942164c95db60f3f5aa88a99f76b525994d194e9f5f9df387ea` |
| 글리프오버라이드 | `064a25fcec96572e2ab68ac76602530eef37099e5b673431eab13f8d821b3781` |

프로젝트루트, Python3.12/Pillow/py65, 보존원본·CSV·폰트·토큰목록이 필요하다. 사용자 적용은 동봉Windows도구만으로 가능하다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify_source.ps1
python scripts/build_dialogue_footer_fix.py --active-font-nops 2 --output build/dialogue_footer_repro_next
python scripts/verify_dialogue_footer_abi.py --build build/dialogue_footer_repro_next --output qa/reports/dialogue_footer_abi_next.json
python work/hamton_fix_20261004/verify_footer_runtime.py
```

빌더와 QA의 출력은 새경로를 요구한다. 이미 생성된 보고서는 덮어쓰지 않는다. 실제 입력과 장면스킵/에뮬레이터/캡처스크립트는 각 QA 폴더의 environment.json과controller_plan/scene_skip.csv 및 스냅샷을 따른다. 새 경로로 캡처를 재실행할 때 런타임 보고서의 경로도 해당 후보에 맞게 변경한다.

**다음 작업 하나: 사용자 Mesen에서 v1.0.1을 새로 적용한 ROM을 처음부터 실행하여30개 교환 후 대기 문구를 확인한다.**
