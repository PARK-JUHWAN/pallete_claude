# Palette Template - App Store Screenshot Generator

**범용 다국어 App Store 스크린샷 자동 생성 시스템.**

---

## 이 패키지는 무엇인가

영문 슬로건 JSON과 mockup 이미지를 받아서 39개국 (또는 N개국) 스크린샷 PNG를 자동 생성하는 도구이다.

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

## 사용자 vs Claude 역할 분담

| 폴더 | 사용자(osk)가 준비 | Claude / Claude Code가 자동 생성 |
|------|--------------------|----------------------------------|
| `fonts/` | ✅ ttf 파일 | — |
| `ingredient/` | ✅ mockup PNG 6장 | — |
| `source/` | ✅ 영문 슬로건 JSON (`en-US.json`) | — |
| `output/` | — | ✅ 언어별 텍스트 폴더 (source 보고 ASO 번역) |
| `screenshots/` | — | ✅ PNG 결과물 (스크립트 자동 생성) |

→ **사용자는 fonts / ingredient / source 3개만 채우면 끝.**
→ output 과 screenshots 는 자동 생성됨.

---

## 시작 가이드 (5단계)

### 1단계: 폰트 준비 (`fonts/`)

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

### 2단계: Mockup 준비 (`ingredient/`)

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

### 3단계: 영문 슬로건 준비 (`source/`)

`source/en-US.json` 파일을 작성한다. 형식:

```json
{
  "en-US": {
    "slogan_1": [
      "First line of slogan 1",
      "Second line of slogan 1"
    ],
    "slogan_2": [
      "First line of slogan 2",
      "Second line of slogan 2"
    ],
    "slogan_3": [
      "First line of slogan 3",
      "Second line of slogan 3"
    ]
  }
}
```

- `slogan_1` ~ `slogan_3`: 각 슬로건은 정확히 2줄
- 각 슬로건이 1, 2, 3번 PNG에 들어감
- 영문 ASO 키워드 강하게 작성 권장

### 4단계: Claude / Claude Code 가 자동 처리

사용자가 위 3개 폴더(fonts, ingredient, source) 채우면 Claude 가:

1. **`source/en-US.json` 분석** → 영문 슬로건 의도 파악
2. **N개 언어 ASO 번역** → 각 언어권 검색 키워드 중심 재구성
3. **`output/` 폴더 자동 생성**:
   ```
   output/
   ├── 1_en/
   │   ├── 1_en_1.txt    (slogan_1의 2줄)
   │   ├── 1_en_2.txt    (slogan_2의 2줄)
   │   └── 1_en_3.txt    (slogan_3의 2줄)
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

⚠️ **언어 코드는 underscore 유지** (`es_MX`, `pt_BR`, `zh_Hans`).
ASC API 는 hyphen (`es-MX`) 사용하므로 변환 주의.

### 5단계: 합성 실행

`make_screenshots.py` 의 `LANG_TO_FONT` 딕셔너리에 사용 언어 매핑 확인 후:

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
