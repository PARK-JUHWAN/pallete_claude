# Palette - App Store Screenshot Generator

다국어 App Store 스크린샷 자동 생성 시스템.

영문 슬로건 JSON과 mockup 이미지를 받아 N개 언어의 PNG (각 6장) 를 자동 생성한다.

- iPhone: 1242 x 2688 (3장)
- iPad: 2048 x 2732 (3장)
- 언어 N개
- 총 출력: N × 6장

---

## 폴더 구조

```
{프로젝트}/
├── fonts/                      # 폰트 파일 (사용자 준비, Black weight 권장)
├── ingredient/                 # mockup PNG 6장 (사용자 준비)
│   ├── iphone_1.png
│   ├── iphone_2.png
│   ├── iphone_3.png
│   ├── ipad_1.png
│   ├── ipad_2.png
│   └── ipad_3.png
├── source/                     # 영문 슬로건 JSON (사용자 준비)
│   └── en-US.json              # slogan_1, slogan_2, slogan_3 (각 2줄)
├── output/                     # 언어별 텍스트 폴더 (Claude 자동 생성)
│   ├── 1_xx/
│   │   ├── 1_xx_1.txt          # 1번 PNG에 들어갈 2줄
│   │   ├── 1_xx_2.txt          # 2번 PNG에 들어갈 2줄
│   │   └── 1_xx_3.txt          # 3번 PNG에 들어갈 2줄
│   └── ... (언어별 폴더)
├── screenshots/                # 결과물 (스크립트 자동 생성)
│   └── {번호}_{언어코드}/
│       ├── {번호}_{언어코드}_iphone_1.png
│       ├── {번호}_{언어코드}_iphone_2.png
│       ├── {번호}_{언어코드}_iphone_3.png
│       ├── {번호}_{언어코드}_ipad_1.png
│       ├── {번호}_{언어코드}_ipad_2.png
│       └── {번호}_{언어코드}_ipad_3.png
├── make_screenshots.py
├── verify_screenshots.py
├── CLAUDE.md
├── VERIFY.md
├── README.md
├── LESSONS_LEARNED.md
└── requirements.txt
```

---

## source/en-US.json 형식

사용자가 작성하는 입력 파일.

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

각 슬로건은 정확히 2줄. 1, 2, 3번 PNG 슬롯에 각각 매핑.

---

## Claude 작업 흐름

### 1. source/en-US.json 분석
영문 슬로건 3개 의도 파악. ASO 핵심 키워드 추출.

### 2. N개 언어 ASO 번역
각 언어권 사용자가 실제 검색하는 단어 중심 재구성.
- 직역 / 의역 금지
- ASO 키워드 우선
- 자세한 ASO 원칙은 `json/TRANSLATION_GUIDE.md` 참고

### 3. output/ 폴더 자동 생성
번역된 결과를 텍스트 파일로 저장:

```
output/{번호}_{언어}/{번호}_{언어}_1.txt   ← slogan_1 번역 (2줄)
output/{번호}_{언어}/{번호}_{언어}_2.txt   ← slogan_2 번역 (2줄)
output/{번호}_{언어}/{번호}_{언어}_3.txt   ← slogan_3 번역 (2줄)
```

⚠️ 언어 코드는 underscore (`es_MX`, `pt_BR`, `zh_Hans`).
ASC API는 hyphen 사용하니 변환 주의.

### 4. make_screenshots.py 실행
output/ 의 각 텍스트를 mockup에 합성하여 screenshots/ 에 PNG 저장.

---

## 입력 → 출력 매핑

```
output/{번호}_{언어}/{번호}_{언어}_1.txt  →  ingredient/iphone_1.png  →  screenshots/{번호}_{언어}/{번호}_{언어}_iphone_1.png
output/{번호}_{언어}/{번호}_{언어}_1.txt  →  ingredient/ipad_1.png    →  screenshots/{번호}_{언어}/{번호}_{언어}_ipad_1.png
output/{번호}_{언어}/{번호}_{언어}_2.txt  →  ingredient/iphone_2.png  →  screenshots/{번호}_{언어}/{번호}_{언어}_iphone_2.png
output/{번호}_{언어}/{번호}_{언어}_2.txt  →  ingredient/ipad_2.png    →  screenshots/{번호}_{언어}/{번호}_{언어}_ipad_2.png
output/{번호}_{언어}/{번호}_{언어}_3.txt  →  ingredient/iphone_3.png  →  screenshots/{번호}_{언어}/{번호}_{언어}_iphone_3.png
output/{번호}_{언어}/{번호}_{언어}_3.txt  →  ingredient/ipad_3.png    →  screenshots/{번호}_{언어}/{번호}_{언어}_ipad_3.png
```

→ 각 언어당 6장. N개 언어 × 6장 = N × 6장.

---

## 픽셀 규격 (절대 변경 금지)

### iPhone

| 항목 | 값 |
|------|-----|
| 캔버스 크기 | 1242 x 2688 |
| 텍스트 영역 (좌측 마진) | 100 |
| 텍스트 영역 (우측 마진) | 100 |
| 텍스트 영역 (위 마진) | 200 |
| 텍스트 영역 (아래 마진) | 1750 |
| 텍스트 영역 (계산된 좌표) | x: 100~1142, y: 200~938 |
| 텍스트 영역 (계산된 너비/높이) | 1042 x 738 |

### iPad

| 항목 | 값 |
|------|-----|
| 캔버스 크기 | 2048 x 2732 |
| 텍스트 영역 (좌측 마진) | 200 |
| 텍스트 영역 (우측 마진) | 200 |
| 텍스트 영역 (위 마진) | 200 |
| 텍스트 영역 (아래 마진) | 1850 |
| 텍스트 영역 (계산된 좌표) | x: 200~1848, y: 200~882 |
| 텍스트 영역 (계산된 너비/높이) | 1648 x 682 |

### 코드 내 하드코딩 형식

```python
IPHONE = {
    "canvas": (1242, 2688),
    "safe_zone": {
        "x_min": 100,
        "x_max": 1142,
        "y_min": 200,
        "y_max": 938,
        "width": 1042,
        "height": 738,
    },
}

IPAD = {
    "canvas": (2048, 2732),
    "safe_zone": {
        "x_min": 200,
        "x_max": 1848,
        "y_min": 200,
        "y_max": 882,
        "width": 1648,
        "height": 682,
    },
}
```

> **주의:** 위 Safe Zone 값은 mockup 이미지의 텍스트 영역과 일치해야 한다. 사용 중인 mockup의 텍스트 영역이 다르면 이 값을 mockup에 맞게 조정해야 한다.

---

## 텍스트 스타일 (절대 변경 금지)

| 항목 | 값 |
|------|-----|
| Font weight | Black (900) |
| Font color | #FFFFFF (white) |
| Stroke (외곽선) | 없음 |
| 정렬 | 가운데 정렬 (수평 + 수직) |
| Line height | 1.3 |
| 줄 수 | 정확히 2줄 (긴 텍스트만 자동 줄바꿈으로 3~4줄 허용) |

### 그림자

| 항목 | 값 |
|------|-----|
| Color | #1A1A1A |
| Offset X | +4 |
| Offset Y | +4 |
| Opacity | 35% |
| Blur | 20 (Gaussian) |

### 그림자 구현 방법

**중요:** 그림자는 별도 레이어에 그린 뒤 Gaussian blur 적용 후 합성한다. 단순히 그림자 텍스트를 옆에 그리면 "글자 두 번 찍힌" 느낌이 난다.

```python
from PIL import Image, ImageDraw, ImageFilter

# 1. 그림자 전용 레이어 생성
shadow_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
shadow_draw = ImageDraw.Draw(shadow_layer)

# 2. 그림자 텍스트 그리기 (offset 적용)
shadow_draw.text(
    (text_x + 4, text_y + 4),
    text,
    font=font,
    fill=(26, 26, 26, int(255 * 0.35))  # #1A1A1A, 35% opacity
)

# 3. Gaussian blur 적용
shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(20))

# 4. 베이스에 합성
base.alpha_composite(shadow_layer)

# 5. 그 위에 sharp white text 그리기
draw = ImageDraw.Draw(base)
draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255))
```

---

## 폰트 크기 정책

### 시작값
- iPhone: **130pt**
- iPad: **180pt**

### 자동 축소 알고리즘
1. 시작 폰트 크기로 두 줄 너비 측정
2. 두 줄 중 더 긴 줄이 Safe Zone 너비를 초과하면 → **5pt씩 감소**
3. 두 줄 모두 Safe Zone 안에 들어올 때까지 반복
4. **50pt 이하로 떨어지면** → 자동 줄바꿈 시도
5. 자동 줄바꿈해도 안 되면 → skip + 로그 기록
6. 두 줄은 항상 **동일한 폰트 크기** 사용 (더 긴 줄 기준)

### 폰트 크기 범위
- 최대: 130pt (iPhone) / 180pt (iPad)
- 최소: 50pt (iPhone, iPad 동일)

---

## 자동 줄바꿈 알고리즘

50pt에서도 line1 또는 line2가 Safe Zone 너비를 초과하면:

1. 어느 줄이 초과했는지 확인
2. 초과한 줄을 **단어 경계에서 절반으로 자름**
3. 분할된 두 부분이 모두 Safe Zone 안에 들어오는지 확인
4. 들어가면 → 출력 (3~4줄로 표시)
5. 안 들어가면 → skip

### 단어 경계 처리

| 언어 | 분할 기준 |
|------|-----------|
| 라틴/유럽어 | 공백(스페이스) 기준 |
| CJK (ja, zh) | 공백 없음 → 글자 수 기준 절반 |
| RTL (ar, ur, he) | 공백 기준 + bidi 재처리 |
| 인도계 | 대부분 공백 있음 → 라틴어와 동일 |

---

## 폰트 매핑 (LANG_TO_FONT)

언어 코드 → 폰트 파일 매핑은 `make_screenshots.py` 안의 `LANG_TO_FONT` 딕셔너리에서 정의한다.

### 권장 매핑 (Noto Sans 패밀리)

```python
LANG_TO_FONT = {
    # 라틴/유럽/키릴/그리스 (한 폰트로 다수 언어 커버)
    "en": "NotoSans-Black.ttf",
    "es": "NotoSans-Black.ttf",
    "fr": "NotoSans-Black.ttf",
    "de": "NotoSans-Black.ttf",
    # ... 라틴 알파벳 사용 언어 모두

    # CJK
    "ko": "NotoSansKR-Black.ttf",
    "ja": "NotoSansJP-Black.ttf",
    "zh_Hans": "NotoSansSC-Black.ttf",
    "zh_Hant": "NotoSansTC-Black.ttf",

    # 중동
    "ar": "NotoSansArabic-Black.ttf",
    "ur": "NotoSansArabic-Black.ttf",
    "he": "NotoSansHebrew-Black.ttf",

    # 동남아
    "th": "NotoSansThai-Black.ttf",

    # 인도계 (각 언어별 별도 폰트)
    "hi": "NotoSansDevanagari-Black.ttf",
    "mr": "NotoSansDevanagari-Black.ttf",
    "bn": "NotoSansBengali-Black.ttf",
    "gu": "NotoSansGujarati-Black.ttf",
    "pa": "NotoSansGurmukhi-Black.ttf",
    "ta": "NotoSansTamil-Black.ttf",
    "te": "NotoSansTelugu-Black.ttf",
    "kn": "NotoSansKannada-Black.ttf",
    "ml": "NotoSansMalayalam-Black.ttf",
    "or": "NotoSansOriya-Black.ttf",

    # 그루지야어
    "ka": "NotoSansGeorgian-Black.ttf",
}
```

각 프로젝트에서 사용할 언어에 맞게 추가/제거.

---

## RTL (오른쪽→왼쪽) 언어 처리

`ar`(아랍어), `ur`(우르두어), `he`(히브리어)는 RTL 언어이며 글자 모양이 위치에 따라 변형된다(특히 아랍어).

### 필요 라이브러리
```
pip install python-bidi arabic-reshaper
```

### 처리 방법
```python
import arabic_reshaper
from bidi.algorithm import get_display

RTL_LANGS = {"ar", "ur", "he"}

def prepare_text(text, lang):
    if lang in RTL_LANGS:
        if lang in {"ar", "ur"}:
            text = arabic_reshaper.reshape(text)
        text = get_display(text)
    return text
```

가운데 정렬이라 시각적으로는 큰 차이 없어 보이지만, 글자 연결과 형태 정확성을 위해 반드시 처리할 것.

---

## 출력 파일명 규칙 (절대 변경 금지)

```
screenshots/
└── {번호}_{언어코드}/
    ├── {번호}_{언어코드}_iphone_1.png
    ├── {번호}_{언어코드}_iphone_2.png
    ├── {번호}_{언어코드}_iphone_3.png
    ├── {번호}_{언어코드}_ipad_1.png
    ├── {번호}_{언어코드}_ipad_2.png
    └── {번호}_{언어코드}_ipad_3.png
```

언어 코드의 underscore (`es_MX`, `pt_BR`, `zh_Hans`, `en_GB`)는 **그대로 유지**한다.

---

## 합성 동작 흐름

```
[1] output/{번호}_{언어}/{번호}_{언어}_{1|2|3}.txt 읽기
      → 2줄의 텍스트 추출

[2] RTL 언어면 텍스트 재구성

[3] 폰트 파일 로드 (LANG_TO_FONT 매핑)

[4] iPhone 작업:
    - ingredient/iphone_{1|2|3}.png 로드 (원본은 건드리지 않음)
    - 폰트 크기 자동 결정 (130 → 50까지 5pt씩 감소)
    - 50pt에서도 안 맞으면 자동 줄바꿈 시도
    - 그림자 그리기 (별도 레이어 + Gaussian blur)
    - 텍스트 그리기 (white, 가운데 정렬, 수직 중앙)
    - PNG 저장

[5] iPad 작업:
    - ingredient/ipad_{1|2|3}.png 로드
    - 폰트 크기 자동 결정 (180 → 50까지 5pt씩 감소)
    - 동일한 방식으로 합성
    - PNG 저장

[6] 진행 상황 출력:
    [1/N] 1_xx       iphone(3/3) ipad(3/3) ✓
    [2/N] 2_yy       iphone(3/3) ipad(3/3) ✓
    ...

[7] 에러 발생 시 로그:
    [WARN] N_xx/N_xx_2.txt → 50pt에서도 안 맞고 줄바꿈도 실패 (skip)
```

---

## 출력 파일 사양

- **포맷**: PNG
- **픽셀 크기**: 정확히 1242x2688 (iPhone) / 2048x2732 (iPad)
- **resize 금지**: PIL `save()` 시 크기 변경 금지
- **JPG 변환 금지**

---

## 작업 순서

```
1. requirements.txt 통해 의존성 설치 (Pillow, python-bidi, arabic-reshaper)
2. fonts/ 폴더에 ttf 파일 준비 (사용자)
3. ingredient/ 폴더에 mockup PNG 6장 준비 (사용자)
4. source/en-US.json 작성 (사용자) — slogan_1~3 각 2줄
5. Claude 가 N개 언어 ASO 번역 → output/ 자동 생성
6. make_screenshots.py 의 LANG_TO_FONT 확인
7. 1개 언어 테스트: python make_screenshots.py --lang 1_xx
8. 결과 확인 (시각적 검수 권장)
9. 전체 실행: python make_screenshots.py
10. 검증: python verify_screenshots.py
```

---

## 주의사항

- **Safe Zone 좌표** — mockup 이미지의 텍스트 영역과 일치해야 함. mockup이 다르면 이 값을 mockup에 맞게 조정.
- **폰트 크기 50pt 이하 강제 출력 금지** — 가독성 저하
- **3줄/4줄 출력은 자동 줄바꿈 발동 시에만** — 평소엔 2줄 유지
- **mockup 원본 파일(`ingredient/`) 수정 금지** — 항상 새로 로드
- **출력 PNG 크기 변경 금지** — App Store 규격 준수

---

## 검증된 정책 변천사 요약

자세한 내용은 `LESSONS_LEARNED.md` 참고.

```
1차 시도: Safe Zone 175/500 마진, FONT_MIN 70pt, 그림자 offset 25 + blur 0
  → 성공률 25%, 그림자 두 번 찍힌 느낌

2차 시도: FONT_MIN 60pt + 자동 줄바꿈 추가
  → 성공률 98%, 그림자 여전히 어색

3차 시도 (현재): Safe Zone 100/200 마진, FONT_MIN 50pt, 그림자 offset 4 + blur 20
  → 성공률 100%, 그림자 자연스러움
```

새 프로젝트는 처음부터 3차 정책으로 시작할 것.
