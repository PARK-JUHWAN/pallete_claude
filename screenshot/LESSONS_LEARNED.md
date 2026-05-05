# Lessons Learned - Palette System v3

이 문서는 Palette 시스템이 1차 시도(성공률 25%) → 3차 시도(성공률 100%)로 발전하는 과정에서 배운 교훈을 정리한 것이다.

**새 프로젝트는 처음부터 v3 정책을 그대로 사용하면 1번에 100% 달성 가능.**

---

## 함정 1: FONT_MIN을 너무 빡빡하게 잡지 마라

### 1차 시도 (실패)
```python
FONT_MIN = 70
```

**결과:** 288장 중 216장 skip (75% 실패).

**원인:** 
- 독일어, 핀란드어 등 라틴 알파벳 긴 단어
- 인도계 언어 (말라얄람, 타밀)의 합성 글자 폭
- 위 언어들이 70pt에서 Safe Zone 너비 초과

### 3차 시도 (성공)
```python
FONT_MIN = 50
```

**결과:** 288장 중 0장 skip (100% 성공, 자동 줄바꿈 도움).

### 교훈
**처음부터 FONT_MIN = 50 으로 시작하라.** 50pt도 모바일 화면에서 충분히 가독성 있다.

---

## 함정 2: Safe Zone 마진을 너무 크게 잡지 마라

### 1차 시도 (실패)
```python
IPHONE_MARGIN = 175  # 좌우
IPAD_MARGIN = 500    # 좌우
```

**결과:**
- iPhone 사용 가능 너비: 892px (전체 1242 중 71.8%)
- iPad 사용 가능 너비: 1048px (전체 2048 중 51.2%) — **절반이 비어있음**

**iPad가 특히 문제.** 좌우로 1000px이 빈 공간으로 낭비됨.

### 3차 시도 (성공)
```python
IPHONE_MARGIN = 100  # 좌우
IPAD_MARGIN = 200    # 좌우
```

**결과:**
- iPhone 사용 가능 너비: 1042px (+17%)
- iPad 사용 가능 너비: 1648px (+57%)

### 교훈
**iPad의 Safe Zone 마진은 200px 정도면 충분.** mockup이 일반적으로 가운데 정렬되어 있어, 상단 텍스트 영역에서는 좌우 200px 마진이 mockup을 침범하지 않는다.

다만 사용 중인 mockup의 텍스트 영역이 좁다면 이 값을 조정해야 한다. **mockup의 실제 디자인을 확인하고 결정할 것.**

---

## 함정 3: 그림자 흐림(blur)을 0으로 두지 마라

### 1차 시도 (실패)
```python
SHADOW = {
    "color": "#2D2D2D",
    "offset_x": 17,
    "offset_y": 17,
    "opacity": 40,
    "blur": 0,
}
```

**결과:** "글자 두 번 찍힌" 듯한 디자인. 그림자가 너무 또렷해서 텍스트 가독성 해침.

### 3차 시도 (성공)
```python
SHADOW = {
    "color": "#1A1A1A",
    "offset_x": 4,
    "offset_y": 4,
    "opacity": 35,
    "blur": 20,
}
```

**결과:** 자연스럽게 깔린 부드러운 그림자. 텍스트 깊이감만 줌.

### 교훈
**Blur는 절대 0으로 두지 마라.** 최소 12 이상, 권장 20.

또한:
- offset은 작게 (4~6 정도) — 글자에 가까이 붙어야 자연스러움
- opacity는 35% 정도 — blur 강하면 더 진해 보이므로 너무 높지 않게
- color는 더 어둡게 (#1A1A1A) — blur 적용 시 옅어지므로 보상

### 구현 주의사항

**그림자는 별도 레이어에 그리고 Gaussian blur 적용 후 합성해야 한다.**

```python
# ❌ 나쁜 예 (글자 두 번 찍힌 느낌)
draw.text((x+25, y+25), text, font=font, fill="#2D2D2D")  # 그림자
draw.text((x, y), text, font=font, fill="#FFFFFF")         # 텍스트

# ✅ 좋은 예 (자연스러운 그림자)
shadow_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
shadow_draw = ImageDraw.Draw(shadow_layer)
shadow_draw.text((x+4, y+4), text, font=font, fill=(26, 26, 26, 89))  # 35% opacity
shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(20))
base.alpha_composite(shadow_layer)

draw = ImageDraw.Draw(base)
draw.text((x, y), text, font=font, fill=(255, 255, 255))
```

---

## 함정 4: 자동 줄바꿈은 최후 수단으로 두라

### 잘못된 우선순위
```
1. FONT_MIN 70pt 시도
2. 안 되면 자동 줄바꿈 발동 (3~4줄로 표시)
```

**문제:** 줄바꿈 발동 시 한 줄짜리 줄도 작은 폰트로 표시됨. 답답함.

### 올바른 우선순위
```
1. 폰트 크기 130pt → 50pt까지 5pt씩 시도
2. 50pt에서도 안 들어가면 → 자동 줄바꿈 시도
3. 줄바꿈해도 안 되면 → skip
```

### 교훈
**가능한 한 폰트 크기로 해결하고, 줄바꿈은 진짜 마지막 수단으로.**

App Store 스크린샷은 **2줄 큰 글씨가 표준**. 3~4줄로 표시되면 임팩트 떨어짐.

---

## 함정 5: 폰트 크기 시작값을 보수적으로 잡지 마라

### 잘못된 접근
"안 맞을까봐" 시작 폰트를 110pt로 잡았더니, 짧은 텍스트(CJK)도 110pt로 출력됨. 너무 작음.

### 올바른 접근
시작값을 **충분히 크게** 잡고, 자동 축소 알고리즘이 알아서 줄이게 한다.

```python
IPHONE_FONT_START = 130  # iPhone Safe Zone 너비 1042 기준
IPAD_FONT_START = 180    # iPad Safe Zone 너비 1648 기준
```

짧은 텍스트는 시작값 그대로 사용 → 큰 글씨로 임팩트.
긴 텍스트는 자동으로 작아짐 → 안 깨짐.

### 교훈
**시작값은 Safe Zone 너비에 맞춰 충분히 크게.** 알고리즘 신뢰하라.

---

## 함정 6: ko/en을 빠뜨리는 흔한 실수

48개국어 자동화하다가 **본진(영어/한국어)을 까먹는** 일이 자주 발생한다.

### 예방
- 출시 언어 리스트를 미리 명확히 정리
- 자동화 대상에 영어/한국어 포함 여부 확인
- 폰트 매핑(LANG_TO_FONT)에 ko, en 둘 다 포함됐는지 체크

### 한국어 폰트
한국어는 `NotoSansKR-Black.ttf` 별도 다운로드 필요 (CJK 별도).
🔗 https://fonts.google.com/download?family=Noto%20Sans%20KR

---

## 함정 7: PNG 픽셀 크기 절대 변형 금지

App Store 업로드는 **정확한 픽셀 크기**를 요구한다.
- iPhone 6.7": 1290 x 2796 또는 1242 x 2688
- iPad 13": 2064 x 2752 또는 2048 x 2732

PIL의 `save()` 시 **resize되지 않도록** 주의. 픽셀 1개라도 다르면 업로드 거부.

### 코드 체크포인트
```python
# 합성 후 검증
assert img.size == (1242, 2688), f"iPhone size mismatch: {img.size}"
img.save(output_path, format="PNG", optimize=False)
```

---

## 함정 8: RTL 언어 처리 누락

아랍어(`ar`), 우르두어(`ur`), 히브리어(`he`)는 **오른쪽→왼쪽** 읽기 + 글자 모양이 위치에 따라 변형됨.

### 잘못된 처리 (글자 깨짐)
```python
draw.text((x, y), arabic_text, font=font)
```
→ 글자가 분리된 채로 표시됨.

### 올바른 처리
```python
import arabic_reshaper
from bidi.algorithm import get_display

if lang in {"ar", "ur"}:
    text = arabic_reshaper.reshape(text)
text = get_display(text)
draw.text((x, y), text, font=font)
```

가운데 정렬이라 시각적 차이가 작아 보일 수 있지만, **글자 형태 자체가 달라짐.** 반드시 처리할 것.

---

## 정착된 v3 정책 요약

```python
# Safe Zone (mockup 디자인에 따라 조정 필요)
IPHONE_SAFE_ZONE = {"x_min": 100, "x_max": 1142, "y_min": 200, "y_max": 938}
IPAD_SAFE_ZONE = {"x_min": 200, "x_max": 1848, "y_min": 200, "y_max": 882}

# 폰트
IPHONE_FONT_START = 130
IPAD_FONT_START = 180
FONT_MIN = 50
FONT_STEP = 5

# 그림자
SHADOW = {
    "color": "#1A1A1A",
    "offset_x": 4,
    "offset_y": 4,
    "opacity": 35,  # %
    "blur": 20,
}
```

이 값들이 50개 언어 (Palette 프로젝트) 에서 100% 성공률을 달성한 검증된 값이다.

---

## 새 프로젝트 시작 시 체크리스트

- [ ] CLAUDE.md, VERIFY.md, README.md, LESSONS_LEARNED.md 모두 읽음
- [ ] requirements.txt 의존성 설치 (Pillow, python-bidi, arabic-reshaper)
- [ ] fonts/ 폴더에 필요한 ttf 파일 모두 준비 (한국어 포함 확인)
- [ ] ingredient/ 폴더에 mockup PNG 6장 준비, 픽셀 크기 정확히 확인
- [ ] mockup 의 실제 텍스트 영역과 Safe Zone 좌표 일치 여부 확인
- [ ] output/ 폴더에 언어별 텍스트 폴더 생성 (영어/한국어 빠뜨리지 않기)
- [ ] LANG_TO_FONT 딕셔너리에 모든 사용 언어 매핑
- [ ] RTL 언어 사용 시 처리 코드 포함 확인
- [ ] 1개 언어로 먼저 테스트 → 시각적 검수
- [ ] OK 후 전체 실행
- [ ] verify_screenshots.py 로 검증

---

## 시행착오 통계

| 시도 | 정책 변경 | 성공률 | 주요 문제 |
|------|-----------|--------|-----------|
| 1차 | FONT_MIN=70, margin 175/500, blur 0 | 25.0% (72/288) | 폰트 너무 큼, 그림자 어색 |
| 2차 | FONT_MIN=60 + 자동 줄바꿈 | 98.3% (283/288) | 그림자 여전히 어색 |
| 3차 | margin 100/200, FONT_MIN=50, blur 20 | **100.0% (288/288)** | 정착 |

**3번의 시도, 약 1일 소요.** 새 프로젝트는 v3 정책으로 시작하면 1번에 100% 가능.
