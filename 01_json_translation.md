# 1차 작업: JSON 메타데이터 39국 ASO 번역

## 작업 목표

`json/source/en-US.json` 의 영문 메타데이터를 39개 locale 로 ASO 번역하여
`json/locales.json` 생성. main 브랜치에 직접 push.

---

## 1단계: 컨텍스트 파악

다음을 순서대로 읽는다:
1. `README.md` (최상위) — 두 작업 구조 이해
2. `json/README.md` — JSON 작업 명세 (ASO-First 정책)
3. `json/TRANSLATION_GUIDE.md` — ASO 키워드 가이드 + 39 locale 분할 전략
4. `json/source/README.md` — 입력 파일 형식
5. `json/source/en-US.json` — 영문 베이스 (모든 작업의 시작)
6. `json/verify_locales.py` — 검증 로직

---

## 2단계: 입력 자료 검증

- `json/source/en-US.json` 존재 확인
- 8개 키 모두 채워짐 확인:
  - name, subtitle, promotional_text, description, keywords,
    subscription_name, subscription_display_name, subscription_description

누락 시 osk 에게 알리고 멈춤.

---

## 3단계: 39개 locale 한 번에 작성

### 대상 locale (39개)

```
en-US, ko, ja, zh-Hans, zh-Hant, es, es-MX, fr, fr-CA, de-DE,
it, pt-BR, pt-PT, nl, pl, sv, da, nb, fi, cs,
hu, ru, ro, sk, uk, hr, bg, el, ca, en-GB,
ar, he, hi, th, vi, id, ms, tr, ka
```

### 작성 원칙

**en-US:**
- `json/source/en-US.json` 그대로 박기 (변경 없음)
- 8개 키 모두 포함

**38개 비영어 locale (ASO-First 정책):**
- 8개 키 모두 작성 (name + keywords 포함 — 모든 locale 자기 언어 ASO)
- 각 언어권 사용자가 실제 검색하는 단어 중심 ASO 재구성
- 직역 / 의역 절대 금지
- 종 이름 / 도메인 용어는 각 언어권 표준 음차/명칭 사용

### 키별 한도 엄수

| 키 | 한도 |
|---|---|
| name | 30자 |
| subtitle | 30자 |
| promotional_text | 170자 |
| description | 4000자 |
| keywords | 100자 (콤마 구분, 공백 없음) |
| subscription_name | 30자 |
| subscription_display_name | 30자 |
| subscription_description | 1000자 |

### EULA 링크

description 마지막 줄에 반드시 포함:
```
https://www.apple.com/legal/internet-services/itunes/dev/stdeula/
```

### 위험 단어 처리

회피: diagnose, treat, predict, prediction, guaranteed, optimal, AI,
cure, prevent, heal, expert, professional + 각 언어 등가 표현.

영문 베이스 (en-US) 에 잔존 시:
- en-US 는 그대로 유지 (변경 금지)
- 비영어 locale 은 등가 안전 표현으로 우회
  - prediction → forecast / estimate / cycle window
  - predict → anticipate / project
  - optimal → recommended / suggested
  - diagnose → assess / evaluate
  - guaranteed → based on / informed by

### 분할 전략 (timeout 회피)

- 5 locale 씩 그룹 단위로 작성
- 각 그룹 작성 후 `json/locales.json` 에 누적 병합 (즉시 디스크 저장)
- 중간 commit / push 안 함
- 39 locale 모두 완료 후 단일 commit
- timeout 발생 시 이미 작성된 locale 은 skip 하고 빠진 부분부터 채울 것

---

## 4단계: 검증

```bash
python json/verify_locales.py json/locales.json
```

PASS 받기. FAIL 시 자동 수정 후 재검증.

검증 항목:
1. JSON 유효성
2. 39개 locale 일치
3. 모든 locale 8개 키 보유 (ASO-First)
4. 글자수 한도
5. 영문 위험 단어 (warning, fail 처리 X)

영문 위험 단어 warning 은 무시 (en-US 베이스 그대로 유지 정책).

---

## 5단계: Git Push

main 브랜치에 직접 push 시도. 시스템 정책상 별도 브랜치 강제되면 그대로 진행
(osk 가 PR 또는 로컬 머지).

```bash
git add json/locales.json
git commit -m "Add JSON: 39 locales metadata (ASO-optimized)"
git push origin main
```

---

## 6단계: 최종 보고 (표 형식)

| 항목 | 결과 |
|------|------|
| 총 locale 수 | 39 / 39 |
| 모든 locale 8개 키 보유 | 39 / 39 |
| verify_locales.py | PASS / FAIL |
| 글자수 한도 위반 | 0 |
| 영문 위험 단어 우회 처리 | (개수) |
| Git 커밋 | (해시) |
| Push 브랜치 | main / (브랜치명) |

**파일 URL**:
https://github.com/PARK-JUHWAN/pallete_claude/blob/main/json/locales.json

---

## 작업 원칙

- 중간 멈춤 없음
- 사용자 확인 없음
- 자동으로 끝까지 진행
- 에러 발생 시 자동 복구 + 재시도
- 마지막에 표 보고만
- timeout 끊겨도 이어서 작업 가능 (이미 작성된 locale skip)
