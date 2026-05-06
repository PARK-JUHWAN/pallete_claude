# 2차 작업: 스크린샷 39국 ASO 번역 + 234장 PNG 합성

## 작업 목표

`screenshot/source/en-US.json` 의 영문 슬로건을 39개 locale 로 ASO 번역하여
`screenshot/output/` 채우고, 234장 PNG 합성. main 브랜치에 직접 push.

전제: 1차 작업 (json/locales.json) 이미 완료됨. 같은 ASO 키워드 일관성 유지용 참조.

---

## 1단계: 컨텍스트 파악

다음을 순서대로 읽는다:
1. `README.md` (최상위) — 두 작업 구조 이해
2. `screenshot/README.md` — 스크린샷 작업 출발점
3. `screenshot/CLAUDE.md` — 작업 명세 (Safe Zone, 폰트 정책, 그림자)
4. `screenshot/VERIFY.md` — 검증 항목
5. `screenshot/LESSONS_LEARNED.md` — 시행착오 (같은 함정 반복 금지)
6. `screenshot/source/README.md` — 입력 파일 형식
7. `screenshot/source/en-US.json` — 영문 슬로건 베이스
8. `json/locales.json` — 1차 작업 결과물 (ASO 키워드 일관성 참조)

---

## 2단계: 입력 자료 검증

- `screenshot/source/en-US.json` 존재 + slogan_1, slogan_2, slogan_3 각 2줄
- `screenshot/ingredient/` 에 mockup PNG 6장 (iphone_1~3, ipad_1~3)
- `screenshot/fonts/` 에 ttf 파일 (18개 권장)
- `json/locales.json` 존재 (ASO 키워드 참조용)

누락 시 osk 에게 알리고 멈춤.

---

## 3단계: 39국 슬로건 ASO 번역 + output/ 자동 생성

### 대상 locale (39개)

```
en-US, ko, ja, zh-Hans, zh-Hant, es, es-MX, fr, fr-CA, de-DE,
it, pt-BR, pt-PT, nl, pl, sv, da, nb, fi, cs,
hu, ru, ro, sk, uk, hr, bg, el, ca, en-GB,
ar, he, hi, th, vi, id, ms, tr, ka
```

### 작성 원칙

- `screenshot/source/en-US.json` 의 slogan_1, slogan_2, slogan_3 분석
- 각 언어권 ASO 키워드 중심 재구성 (직역 / 의역 X)
- `json/locales.json` 의 같은 locale 키워드와 일관성 유지
- 각 슬로건 정확히 2줄
- 짧고 강한 표현 (스크린샷에 들어갈 시각적 텍스트)

### 출력 구조

```
screenshot/output/
├── 1_en/
│   ├── 1_en_1.txt    (slogan_1 의 2줄, 영문 그대로)
│   ├── 1_en_2.txt    (slogan_2 의 2줄)
│   └── 1_en_3.txt    (slogan_3 의 2줄)
├── 2_ko/
│   ├── 2_ko_1.txt    (slogan_1 한국어 ASO)
│   ├── 2_ko_2.txt
│   └── 2_ko_3.txt
└── ... (39_ka 까지)
```

### 폴더 번호 매핑

```
1=en, 2=ko, 3=ja, 4=zh_Hans, 5=zh_Hant,
6=es, 7=es_MX, 8=fr, 9=fr_CA, 10=de,
11=it, 12=pt_BR, 13=pt_PT, 14=nl, 15=pl,
16=sv, 17=da, 18=nb, 19=fi, 20=cs,
21=hu, 22=ru, 23=ro, 24=sk, 25=uk,
26=hr, 27=bg, 28=el, 29=ca, 30=en_GB,
31=ar, 32=he, 33=hi, 34=th, 35=vi,
36=id, 37=ms, 38=tr, 39=ka
```

### ASC ↔ Palette 코드 변환

⚠️ ASC API 는 hyphen, Palette output 은 underscore. 변환 적용:
- es-MX → 7_es_MX
- zh-Hans → 4_zh_Hans
- zh-Hant → 5_zh_Hant
- pt-BR → 12_pt_BR
- pt-PT → 13_pt_PT
- fr-CA → 9_fr_CA
- en-US → 1_en
- en-GB → 30_en_GB
- de-DE → 10_de

### 텍스트 파일 형식

- 인코딩: UTF-8 (BOM 없음)
- 줄 수: 정확히 2줄
- 빈 줄 없음

### 분할 전략 (timeout 회피)

- 5 locale 씩 그룹 단위로 output/ 폴더 즉시 write
- 각 그룹 작성 후 다음 그룹 자동 진행
- 중간 commit / push 안 함
- 39개 모두 완료 후 단일 commit
- timeout 발생 시 이미 작성된 locale 폴더 skip 하고 빠진 부분부터 채울 것

---

## 4단계: LANG_TO_FONT 매핑 검증

`screenshot/make_screenshots.py` 의 LANG_TO_FONT 딕셔너리 확인.

39개 locale 모두 매핑 존재 여부 검증. 누락 발견 시 자동 추가:
- ka → NotoSansGeorgian-Black.ttf
- nb → NotoSans-Black.ttf
- ca → NotoSans-Black.ttf
- bg → NotoSans-Black.ttf
- en_GB → NotoSans-Black.ttf

폰트 파일 자체가 `screenshot/fonts/` 에 없으면 osk 에게 알리고 멈춤.

---

## 5단계: 합성 실행

```bash
cd screenshot
pip install -r requirements.txt

# 1개 언어 테스트 (1_en)
python make_screenshots.py --lang 1_en
```

→ PNG 6장 생성 확인 + 픽셀 크기 (1242x2688 / 2048x2732) 검증.

```bash
# 전체 실행
python make_screenshots.py
```

→ 39 × 6 = 234장 PNG 생성 예상.

---

## 6단계: 검증

```bash
python verify_screenshots.py
```

PASS 받기. FAIL 시 자동 수정 후 재검증.

검증 항목:
1. 폴더/파일 존재 (39 × 6 = 234)
2. PNG 포맷
3. 픽셀 크기 (iPhone 1242x2688, iPad 2048x2732)
4. 빈 파일 (0바이트)
5. 색상 모드 (RGB/RGBA)
6. skip 로그 (skipped.log)

---

## 7단계: Git Push

main 브랜치에 직접 push 시도. 시스템 정책상 별도 브랜치 강제되면 그대로 진행
(osk 가 PR 또는 로컬 머지).

```bash
git add screenshot/output/ screenshot/screenshots/
git commit -m "Generate screenshots: 39 locales × 6 = 234 PNGs (ASO-optimized)"
git push origin main
```

---

## 8단계: 최종 보고 (표 형식)

| 항목 | 결과 |
|------|------|
| output/ 폴더 생성 | 39 / 39 |
| 텍스트 파일 (39 × 3) | 117 / 117 |
| 합성된 PNG (39 × 6) | 234 / 234 |
| 픽셀 크기 위반 | 0 |
| Skip 발생 | 0 |
| verify_screenshots.py | PASS / FAIL |
| 자동 줄바꿈 발동 | (개수) |
| Git 커밋 | (해시) |
| Push 브랜치 | main / (브랜치명) |

**결과 URL**:
https://github.com/PARK-JUHWAN/pallete_claude/tree/main/screenshot/screenshots

---

## 작업 원칙

- 중간 멈춤 없음
- 사용자 확인 없음
- 자동으로 끝까지 진행
- 에러 발생 시 자동 복구 + 재시도
- 마지막에 표 보고만
- timeout 끊겨도 이어서 작업 가능 (이미 작성된 locale 폴더 skip)
- 1_en 합성 결과는 osk 가 시각 검증할 예정 (Safe Zone 침범 / 글자 깨짐 없는지)
