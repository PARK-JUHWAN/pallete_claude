# Palette Claude - App Store Localization Toolkit

App Store 다국어 출시를 위한 두 가지 자동화 도구를 제공하는 통합 템플릿.

---

## 두 가지 작업

이 레포는 **독립적인 두 가지 공장**으로 구성되어 있다. 필요한 작업만 골라서 진행하면 된다.

### 1. 스크린샷 공장 → `screenshot/`

**다국어 App Store 스크린샷 자동 생성.**

- 입력: mockup PNG 6장 + 언어별 텍스트 파일
- 출력: 언어 × 6장 PNG (iPhone 3장 + iPad 3장)
- 처리: 폰트 자동 매핑, 그림자 합성, 자동 줄바꿈, RTL 처리

지원 항목:
- 픽셀 정확한 PNG 생성 (App Store 규격)
- 50+ 언어 (라틴/CJK/RTL/인도계/태국/그루지야)
- 자동 폰트 크기 조절 (텍스트 길이에 따라)
- Gaussian blur 그림자

→ 작업 시 `screenshot/README.md` 부터 읽기.

### 2. JSON 번역 공장 → `json/`

**App Store Connect (ASC) 메타데이터 39개국 번역.**

- 입력: 영문 스토어 텍스트 (subtitle, description, promo 등)
- 출력: `locales.json` (39개 locale 통합 파일)
- 처리: 번역 규칙 적용, 글자수 한도 검증, 위험 단어 검출

지원 항목:
- ASC 8개 키 (name, subtitle, promotional_text, description 등)
- 38개 비영어 locale 자동 매핑
- ASO 영어 키워드 독점 전략 (name/keywords는 en-US만)
- Apple 심사 위험 단어 자동 검출

→ 작업 시 `json/README.md` 부터 읽기.

---

## 두 작업은 독립적

| 항목 | 스크린샷 | JSON 번역 |
|------|----------|-----------|
| 입력 | mockup PNG + 텍스트 txt | 영문 스토어 텍스트 |
| 출력 | PNG 파일들 | locales.json 1개 |
| 도구 | Pillow, python-bidi | json 표준 라이브러리 |
| 결과물 위치 | `screenshot/screenshots/` | `json/locales.json` |
| ASC 업로드 방식 | App Store Connect 화면 수동/fastlane | ASC API 자동 PUT (별도 스크립트) |

서로 영향 안 줌. 둘 다 할 수도, 하나만 할 수도 있다.

---

## Claude / Claude Code 가 받았을 때

작업 분기:

```
"스크린샷 만들어줘"     → screenshot/ 폴더로 진입 → screenshot/README.md 읽기
"메타데이터 번역해줘"   → json/ 폴더로 진입 → json/README.md 읽기
"둘 다 해줘"            → 각각 독립 진행 (순서 무관)
```

---

## 폴더 구조

```
pallete_claude/
├── README.md                          ← 본 파일
│
├── screenshot/                        ← 스크린샷 공장
│   ├── CLAUDE.md
│   ├── VERIFY.md
│   ├── LESSONS_LEARNED.md
│   ├── README.md                      ← 스크린샷 작업 출발점
│   ├── make_screenshots.py
│   ├── verify_screenshots.py
│   ├── requirements.txt
│   ├── fonts/                         ← 폰트 파일
│   ├── ingredient/                    ← mockup PNG 6장
│   └── output/                        ← 언어별 텍스트 폴더
│
└── json/                              ← JSON 번역 공장
    ├── README.md                      ← 번역 작업 출발점
    ├── TRANSLATION_GUIDE.md
    ├── locales.template.json
    └── verify_locales.py
```

---

## 미래의 클로드들에게

이 레포는 **재사용 가능한 템플릿**이다.

새 앱 작업 시:
1. 이 레포 fork (또는 zip 복사)
2. 앱별 데이터만 교체:
   - `screenshot/ingredient/` 에 새 mockup PNG
   - `screenshot/output/` 에 새 언어별 텍스트
   - `json/locales.json` 에 새 앱 메타데이터
3. 정책/스크립트는 수정 불필요 (검증된 v3 정책)

**시행착오는 다 해놨다.** 새 프로젝트는 처음부터 100% 성공 가능.

---

## 시스템 요구사항

```bash
Python 3.8+
pip install -r screenshot/requirements.txt
```

상세 의존성:
- 스크린샷: Pillow, python-bidi, arabic-reshaper
- JSON: 표준 라이브러리 (json, sys, pathlib) 만 사용

---

## 제작 배경

50앱 프로젝트 (Shift Meal Planner, Reptile Weather 등) 의 다국어 출시 자동화 작업 중 도출된 검증된 시스템.

- 스크린샷: 50개 언어 × 6장 = 300장 출력 검증
- JSON: 39개국 메타데이터 자동 입력 검증

이후 모든 50앱 시리즈에 재사용.
