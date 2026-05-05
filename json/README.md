# JSON Translation Factory (ASO-First)

App Store Connect 39개국 메타데이터 자동 입력을 위한 **ASO 키워드 중심** 번역 + 검증 도구.

---

## 핵심 원칙: ASO 우선 (검색 노출 최적화)

osk 앱은 마이너 시장 (니치 도메인) 대상.
**브랜드 인지도 < 검색 노출** 이 절대 우선.

### 작성 원칙

| 영역 | 원칙 |
|---|---|
| 앱 브랜드명 영문 고집 | ❌ 금지 |
| 직역 (예: "Reptile Weather" → "도마뱀 날씨") | ❌ 금지 |
| 의역 (자연스러운 번역) | ❌ 금지 |
| **해당 언어권 사용자가 실제로 검색하는 단어 우선** | ✅ 필수 |

### 비교 예시 (한국어)

```
기존 의역:
  "Reptile Weather - 파충류 케어 점수"

ASO 우선:
  "파충류 사육 온습도 - 테라리움 관리"
  ↑ 4개 키워드 노출: 파충류 사육 / 온습도 / 테라리움 / 관리
```

각 locale 의 subtitle / description / promotional_text 는 **해당 언어권 검색량 높은 단어** 로 재구성.

---

## 적용 범위

| 키 | 원칙 |
|---|---|
| `name` | en-US 만 (영문 ASO 키워드 — 30자) |
| `keywords` | en-US 만 (검색 키워드 콤마 구분 — 100자) |
| `subtitle` | 각 locale ASO 키워드 풍부하게 (30자) |
| `promotional_text` | 각 locale ASO 키워드 풍부하게 (170자) |
| `description` | 각 locale ASO 키워드 풍부하게 (4000자) |
| `subscription_name` | 영문 유지 OK (구독은 검색 영향 적음) |
| `subscription_display_name` | 각 locale 자연스럽게 |
| `subscription_description` | 각 locale 자연스럽게 |

---

## 폴더 구조

```
json/
├── README.md                    ← 본 파일 (출발점)
├── TRANSLATION_GUIDE.md         ← ASO 키워드 가이드 + 분할 전략
├── locales.template.json        ← JSON 빈 템플릿
└── verify_locales.py            ← JSON 검증 스크립트
```

---

## 작업 순서 (다른 Claude 가 받았을 때)

### 1단계: 입력 자료 확인
osk 가 작성한 영문 스토어 텍스트 파일 (예: `0_store_en_US.txt`).
7섹션 구조: 프로모션 / 설명 / 키워드 / 이름 / 부제 / 구독 / 스크린샷.
스크린샷 텍스트는 본 작업 제외 (트랙 C 별도).

### 2단계: TRANSLATION_GUIDE.md 숙지
ASO 키워드 원칙, 위험 단어, 글자수 한도, 분할 전략 확인.

### 3단계: 각 언어권 검색어 조사 (★ 핵심)
앱 도메인 (예: 파충류 사육, 임신 관리, 운동 트래커 등) 의 핵심 키워드를 각 언어권 별로 조사.

조사 방법:
- App Store 검색 자동완성 (해당 locale 로 설정된 디바이스 또는 시뮬)
- Google 검색 자동완성 + "사람들이 함께 검색한 단어"
- Reddit / 해당 언어권 커뮤니티 사용 빈도 단어
- 위키피디아 해당 언어 페이지의 표제어

osk 가 도메인 핵심 키워드 (영문 5-10개) 를 미리 줬다면 그걸 각 언어로 의역 X / 검색어 매핑.

### 4단계: 템플릿 복사
```bash
cp locales.template.json locales.json
```

### 5단계: en-US 채우기
영문 베이스를 ASO 키워드 강한 표현으로. `name` / `keywords` 에 핵심 키워드 집중.

### 6단계: 38개 비영어 locale 작성 (ASO 키워드 중심)
5개씩 분할 (timeout 회피):
- 그룹 1 (검수 5국): ko, ja, zh-Hans, es-MX, de-DE
- 그룹 2~7: 5개씩
- 그룹 8: 마지막 3국 (ms, tr, ka)

각 그룹 작성 후 main commit + push 권장.
**검수 5국 (그룹 1) 은 osk 직접 검토 후 OK 받아야 다음 그룹 진행.**

### 7단계: 검증
```bash
python verify_locales.py locales.json
```
PASS 받으면 완료.

⚠️ verify_locales.py 는 글자수 / JSON 구조 / 영문 위험 단어만 검증.
**ASO 품질 (검색어 적합성) 은 osk 직접 검수 영역.**

### 8단계: ASC 업로드
별도 스크립트 (`upload_to_asc.py`) 사용. 본 폴더에는 미포함.
osk 가 ASC API .p8 + Issuer ID + Key ID 보유 시 작성 가능.

---

## locale 39개 (ASC 표준 — hyphen)

```
en-US, ko, ja, zh-Hans, zh-Hant, es, es-MX, fr, fr-CA, de-DE,
it, pt-BR, pt-PT, nl, pl, sv, da, nb, fi, cs,
hu, ru, ro, sk, uk, hr, bg, el, ca, en-GB,
ar, he, hi, th, vi, id, ms, tr, ka
```

⚠️ ASC API = hyphen (`es-MX`)
⚠️ Flutter ARB / Palette output/ = underscore (`es_MX`)
혼동 금지.

---

## 다른 앱에서 재사용

본 폴더 통째로 fork → 다른 앱 repo 에 박기.
입력 텍스트 (`0_store_en_US.txt`) 만 갈아끼우면 끝.
TRANSLATION_GUIDE / verify_locales / locales.template 그대로 사용 가능.

⚠️ 단 도메인 (파충류 사육 / 임신 / 피트니스 등) 별로 ASO 키워드는 다르므로,
각 앱마다 osk 가 영문 핵심 키워드 5-10개 미리 제시 권장.
