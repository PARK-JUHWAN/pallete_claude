# Translation Guide — Store Metadata 39 Locales (ASO-First)

## locale 키 형식 (ASC 표준)

ASC API = hyphen. underscore 금지.

✅ `es-MX`, `zh-Hans`, `pt-BR`, `fr-CA`, `de-DE`
❌ `es_MX`, `zh_Hans`, `pt_BR`

(Flutter ARB / Palette output/ 폴더는 underscore — 다른 시스템과 혼동 금지)

---

## 39개 locale

```
en-US, ko, ja, zh-Hans, zh-Hant, es, es-MX, fr, fr-CA, de-DE,
it, pt-BR, pt-PT, nl, pl, sv, da, nb, fi, cs,
hu, ru, ro, sk, uk, hr, bg, el, ca, en-GB,
ar, he, hi, th, vi, id, ms, tr, ka
```

총 39 = en-US 1 + 비영어 38.

---

## 키별 규칙

| 키 | 한도 | en-US | 38 비영어 |
|---|---|---|---|
| name | 30자 | 필수 (ASO 키워드 강하게) | 키 omit |
| keywords | 100자 | 필수 (검색 키워드 콤마 구분) | 키 omit |
| subtitle | 30자 | 필수 (ASO) | 필수 (ASO) |
| promotional_text | 170자 | 필수 (ASO) | 필수 (ASO) |
| description | 4000자 | 필수 (ASO) | 필수 (ASO) |
| subscription_name | 30자 | 필수 | 필수 (영문 유지 OK) |
| subscription_display_name | 30자 | 필수 | 필수 (의역) |
| subscription_description | 1000자 | 필수 | 필수 (의역) |

---

## 핵심 원칙: ASO 우선

### 절대 금지

| 행동 | 금지 이유 |
|---|---|
| 앱 브랜드명 영문 그대로 박기 (예: subtitle 에 "Reptile Weather") | 검색 키워드 자리 낭비 |
| 직역 (예: "Reptile Weather" → "도마뱀 날씨") | 검색량 0 단어 발생 |
| 의역 (예: "Reptile Weather" → "파충류 날씨") | 검색 빈도 낮음 |

### 필수

각 locale 의 subtitle / description / promotional_text 는:
1. 해당 언어권 사용자가 **실제로 검색하는 단어** 우선
2. 도메인 핵심 키워드 (영문 베이스에서 osk 가 제시) 를 각 언어로 ASO 매핑
3. 검색 키워드 4-7개를 자연스럽게 녹임

### 비교 예시 (한국어)

```
[기존 의역 — 금지]
subtitle: "Reptile Weather - 파충류 케어 점수"
   → 검색 노출 거의 0

[ASO 우선 — 권장]
subtitle: "파충류 사육 온습도 - 테라리움 관리"
   → 노출 키워드: 파충류 사육 / 온습도 / 테라리움 / 관리 (4개)
```

---

## ASO 키워드 조사 가이드

각 언어권 작업 전 **검색어 조사 필수**.

### 조사 방법

1. **App Store 검색 자동완성**
   - 디바이스 언어를 해당 locale 로 변경
   - App Store 검색창에 도메인 핵심어 입력
   - 자동완성 + 연관 검색어 확인

2. **Google 검색 자동완성**
   - 해당 언어로 검색
   - "사람들이 함께 검색한 단어" 섹션
   - 페이지 하단 "관련 검색어"

3. **현지 커뮤니티**
   - Reddit (r/[언어권])
   - 일본: 5ch, 한국: 디시인사이드 / 네이버 카페
   - 도메인 관련 자주 등장 단어

4. **위키피디아**
   - 해당 언어 페이지의 표제어
   - 도메인 표준 용어 확인

### 핵심 키워드 매핑

osk 가 영문 핵심 키워드 5-10개를 줬다면, 각 언어로 직역 X / 검색어 매핑:

```
[영문 핵심 키워드 예시 — 파충류 도메인]
- reptile husbandry
- vivarium
- bearded dragon
- humidity tracker
- shed cycle
- UVB
- terrarium care

[한국어 매핑 — 검색량 기반]
- 파충류 사육 (husbandry → 사육이 검색량 높음)
- 테라리움 (vivarium → 테라리움이 일반)
- 비어디드 드래곤 (bearded dragon → 음차 그대로)
- 온습도 (humidity → 온도 + 습도 결합어가 일반)
- 탈피 (shed → 표준어)
- UVB (그대로)
- 사육환경 (terrarium care → 환경 단어)

[일본어 매핑]
- 爬虫類飼育 (husbandry)
- ビバリウム (vivarium 음차)
- フトアゴヒゲトカゲ (bearded dragon)
- 温湿度 (humidity)
- 脱皮 (shed)
- UVB
- 飼育環境
```

---

## 번역 규칙

### 1. 영문 베이스
en-US = ASO 키워드 강한 영문. osk 가 제공한 텍스트 그대로 박기.
`name` 30자 / `keywords` 100자 에 검색 키워드 집중.

### 2. 직역 / 의역 둘 다 금지
"Reptile Weather" 같은 브랜드명을 비영어 locale 에 그대로 박지 않음.
"도마뱀 날씨" 같이 직역하지 않음.
"파충류 날씨" 같이 의역도 안 함 (검색량 낮음).

대신 → 도메인 키워드 (파충류 사육 + 온습도 + 테라리움 등) 로 재구성.

### 3. 글자수 한도 엄수
독일어 / 러시아어 / 핀란드어는 영어 대비 30~50% 길어지는 경향.
한도 초과 시 키워드 우선순위 정리해서 압축.
특히 subtitle 30자 = 가장 빡빡함. 키워드 2-3개로 좁힘.

### 4. 위험 단어 회피

다음 단어 + 각 locale 등가 표현 모두 회피:

```
diagnose, treat, predict, guaranteed, optimal, AI,
cure, prevent, heal, expert, professional
```

이유: Apple 의료 / 건강 앱 가이드라인 위반 가능성.

대체 표현:
- `diagnose` → `estimate`, `assess`, `evaluate`
- `treat` → `support`, `guide`
- `predict` → `forecast`, `anticipate`
- `guaranteed` → `based on`, `informed by`
- `optimal` → `recommended`, `suggested`
- `AI` → 단순 알고리즘 명칭 (`based on weather data`)
- `cure` / `prevent` → `support`, `help`

### 5. EULA 링크 유지
description 마지막 줄:
```
https://www.apple.com/legal/internet-services/itunes/dev/stdeula/
```
모든 locale 동일하게 유지.

### 6. 도메인 특화 용어
앱마다 도메인 특화 용어 (동물 이름, 의료 용어 등) 가 있으면 osk 사전 검수 표 verbatim 적용.
이 부분은 ASO 와 무관 — 정확한 용어 사용.

---

## 분할 전략

한 번에 39 locale 작성 시 stream timeout 위험. 분할 권장.

```
그룹 1 (검수 5국): ko, ja, zh-Hans, es-MX, de-DE
그룹 2: fr, fr-CA, it, es, pt-BR
그룹 3: pt-PT, nl, pl, sv, da
그룹 4: nb, fi, cs, hu, ru
그룹 5: ro, sk, uk, hr, bg
그룹 6: el, ca, en-GB, zh-Hant, ar
그룹 7: he, hi, th, vi, id
그룹 8 (3국): ms, tr, ka
en-US: 영문 베이스 그대로 박기
```

각 그룹 작성 후 main commit 권장.
**검수 5국 = osk 직접 검토 후 OK 받아야 다음 그룹 진행.**

osk 검토 시 확인 항목:
- ASO 키워드가 해당 언어권에서 실제 검색되는지
- 직역 / 의역 한 부분이 없는지
- 도메인 키워드가 자연스럽게 녹았는지
- 글자수 한도 안에 들어왔는지

---

## 출력 형식

```json
{
  "en-US": {
    "name": "...",
    "subtitle": "...",
    "promotional_text": "...",
    "description": "...",
    "keywords": "...",
    "subscription_name": "...",
    "subscription_display_name": "...",
    "subscription_description": "..."
  },
  "ko": {
    "subtitle": "...",
    "promotional_text": "...",
    "description": "...",
    "subscription_name": "...",
    "subscription_display_name": "...",
    "subscription_description": "..."
  }
}
```

비영어 locale 은 `name`, `keywords` 키 자체 생략.

---

## 검증

각 그룹 작성 후:
```bash
python verify_locales.py locales.json
```

PASS 받아야 다음 그룹 진행.

검증 항목:
1. JSON 유효성
2. 39개 locale 키 일치
3. en-US 8개 키 존재
4. 비영어 locale 6개 키 + name/keywords omit
5. 글자수 한도 (subtitle 30, promo 170, description 4000 등)
6. 영문 위험 단어 검출 (warning)

⚠️ ASO 품질 (검색어 적합성) 은 verify_locales.py 가 검증 X.
osk 직접 검수 영역.
