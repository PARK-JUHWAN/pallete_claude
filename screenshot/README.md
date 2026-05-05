# Palette Template - App Store Screenshot Generator

**범용 다국어 App Store 스크린샷 자동 생성 시스템.**

---

## 이 패키지는 무엇인가

번역된 텍스트를 받아서 mockup 이미지 위에 폰트로 합성하여 App Store 업로드용 PNG를 자동 생성하는 도구이다.

- iPhone: 1242 x 2688 (3장)
- iPad: 2048 x 2732 (3장)
- 언어: 사용자가 정하는 만큼 (1개~수십개)
- 출력: `(언어 수) × 6장` PNG

---

## 누가 쓰나

- 50앱 프로젝트 같은 다국어 앱 출시 작업
- App Store Connect 업로드용 스크린샷 일괄 생성
- 텍스트만 바꿔서 여러 앱에 재사용

---

## 사용자가 준비할 것

```
palette_template/
├── fonts/          ← ttf 파일들 넣기 (사용자 준비)
├── ingredient/     ← mockup PNG 6장 넣기 (사용자 준비)
└── output/         ← 언어별 텍스트 폴더 만들기 (사용자 준비)
```

이 3가지 폴더만 채우면 나머지는 자동.

---

## 시작 가이드 (5단계)

### 1단계: 폰트 준비

`fonts/` 폴더에 필요한 ttf 파일을 넣는다.

**기본 권장 폰트** (Google Fonts에서 다운로드, Black weight 사용):

| 언어 | 폰트 파일 |
|------|-----------|
| 라틴/유럽/키릴/그리스 | `NotoSans-Black.ttf` |
| 한국어 | `NotoSansKR-Black.ttf` |
| 일본어 | `NotoSansJP-Black.ttf` |
| 중국어 간체 | `NotoSansSC-Black.ttf` |
| 중국어 번체 | `NotoSansTC-Black.ttf` |
| 아랍어/우르두 | `NotoSansArabic-Black.ttf` |
| 히브리어 | `NotoSansHebrew-Black.ttf` |
| 태국어 | `NotoSansThai-Black.ttf` |
| 힌디/마라티 | `NotoSansDevanagari-Black.ttf` |
| 그루지야어 | `NotoSansGeorgian-Black.ttf` |
| 인도계 (gu/ta/te/kn/ml/bn/pa/or) | 각 언어별 ttf |

다운로드: https://fonts.google.com/noto

각 zip 안에서 `static/` 폴더의 `*-Black.ttf` 만 추출해서 `fonts/` 에 넣는다.

### 2단계: Mockup 준비

`ingredient/` 폴더에 다음 6장 PNG를 넣는다:

```
ingredient/
├── iphone_1.png   (1242 x 2688, 배경 + iPhone mockup, 텍스트 영역 비어있음)
├── iphone_2.png   (1242 x 2688)
├── iphone_3.png   (1242 x 2688)
├── ipad_1.png     (2048 x 2732)
├── ipad_2.png     (2048 x 2732)
└── ipad_3.png     (2048 x 2732)
```

각 mockup은:
- 정확한 픽셀 크기 (App Store 규격)
- 배경색 + 폰 mockup이 합성된 상태
- 텍스트가 들어갈 상단 공간이 비어있음

### 3단계: 텍스트 준비

`output/` 폴더에 언어별 폴더를 만든다.

```
output/
├── 1_en/
│   ├── 1_en_1.txt    (1번째 PNG에 들어갈 2줄)
│   ├── 1_en_2.txt    (2번째 PNG에 들어갈 2줄)
│   └── 1_en_3.txt    (3번째 PNG에 들어갈 2줄)
├── 2_ko/
│   ├── 2_ko_1.txt
│   ├── 2_ko_2.txt
│   └── 2_ko_3.txt
└── ...
```

**규칙:**
- 폴더명 형식: `{번호}_{언어코드}` (예: `1_en`, `15_es_MX`, `29_zh_Hans`)
- 파일명 형식: `{번호}_{언어코드}_{1|2|3}.txt`
- 각 txt 파일은 **정확히 2줄** (UTF-8, BOM 없음)
- 빈 줄 없음

### 4단계: 폰트 매핑 수정

`make_screenshots.py` 의 `LANG_TO_FONT` 딕셔너리에 사용할 언어를 매핑한다.

```python
LANG_TO_FONT = {
    "en": "NotoSans-Black.ttf",
    "ko": "NotoSansKR-Black.ttf",
    "ja": "NotoSansJP-Black.ttf",
    # ... 사용할 언어 모두 추가
}
```

언어 코드는 `output/` 폴더 안의 폴더명과 일치해야 한다 (`1_en` → 키 `en`).

### 5단계: 실행

```bash
pip install -r requirements.txt

# 1개 언어 테스트 (먼저 권장)
python make_screenshots.py --lang 1_en

# 전체 실행
python make_screenshots.py

# 검증
python verify_screenshots.py
```

결과는 `screenshots/` 폴더에 자동 생성된다:

```
screenshots/
├── 1_en/
│   ├── 1_en_iphone_1.png
│   ├── 1_en_iphone_2.png
│   ├── 1_en_iphone_3.png
│   ├── 1_en_ipad_1.png
│   ├── 1_en_ipad_2.png
│   └── 1_en_ipad_3.png
└── ...
```

---

## 더 자세한 가이드

- **`CLAUDE.md`** - 작업 전체 명세 (Safe Zone, 폰트 정책, 그림자 옵션 등)
- **`VERIFY.md`** - 검증 가이드 (288장 검증 항목)
- **`LESSONS_LEARNED.md`** - 시행착오 정리 (1차 25% → 3차 100% 갈 때까지 배운 것)

---

## 주의사항

- **mockup 원본 (`ingredient/`) 절대 수정 금지** — 항상 새로 로드
- **출력 PNG 픽셀 크기 절대 변형 금지** — App Store 규격 위반 시 업로드 불가
- **Safe Zone 좌표는 mockup에 맞춰 검증된 값** — 임의 변경 비추천
- **3줄 이상 출력은 최후 수단** — 가독성 떨어짐, 가능하면 폰트 크기 조절로 해결

---

## 검증된 정책 (3차 시도 끝에 도달)

```
Safe Zone:
  iPhone: 좌우 100px, 위 200px, 아래 1750px
  iPad:   좌우 200px, 위 200px, 아래 1850px

폰트 크기:
  iPhone 시작 130pt, iPad 시작 180pt
  자동 축소 5pt씩, 최소 50pt
  50pt에서도 안 들어가면 자동 줄바꿈

그림자:
  color #1A1A1A, offset (4, 4), opacity 35%, blur 20
```

자세한 변천사는 `LESSONS_LEARNED.md` 참고.

---

## 제작

**Palette 시스템 v3** - 50앱 프로젝트의 첫 번째 자동화 도구로 시작, 다른 앱들에 재사용 가능하도록 범용화됨.
