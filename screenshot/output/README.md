# output/

**이 폴더는 Claude 가 자동 생성합니다.** 사용자가 직접 채우지 않아도 됨.

Claude 가 `source/en-US.json` 의 영문 슬로건을 분석하고, 각 언어로 ASO 번역해서 이 폴더를 채웁니다.

---

## Claude 가 만들어주는 구조

```
output/
├── 1_en/
│   ├── 1_en_1.txt    (slogan_1 의 2줄, 영문 그대로)
│   ├── 1_en_2.txt    (slogan_2 의 2줄)
│   └── 1_en_3.txt    (slogan_3 의 2줄)
├── 2_ko/
│   ├── 2_ko_1.txt    (slogan_1 의 한국어 ASO 번역, 2줄)
│   ├── 2_ko_2.txt
│   └── 2_ko_3.txt
└── ... (사용할 언어 만큼)
```

## 명명 규칙

- 폴더명: `{번호}_{언어코드}`
  - 번호: 정수 (순서, 보통 1부터 시작)
  - 언어코드: BCP-47 또는 자주 쓰는 변형 (예: `en`, `en_GB`, `zh_Hans`, `pt_BR`)
- 파일명: `{번호}_{언어코드}_{1|2|3}.txt`

언어 코드의 underscore는 그대로 유지: `es_MX`, `pt_BR`, `zh_Hans`, `en_GB`

⚠️ **ASC API는 hyphen** (`es-MX`), **여기는 underscore** (`es_MX`). 변환 주의.

## 텍스트 파일 형식

- **인코딩**: UTF-8 (BOM 없음)
- **줄 수**: 정확히 2줄
- **빈 줄 없음**: 파일 시작/끝에 공백 없음
- **각 줄**: 한 PNG에 한 줄로 표시됨

예시 (`output/1_en/1_en_1.txt`):
```
Stop guessing every morning
Get today's care score
```

→ 1번 PNG (iPhone, iPad) 에 위 2줄이 한 화면에 표시됨.

---

## 사용자가 직접 만드는 경우 (선택)

대부분 Claude 가 자동 생성하지만, 수동으로 만들고 싶다면:

1. `source/en-US.json` 보고 슬로건 3개 (각 2줄) 확인
2. 위 폴더/파일 구조 그대로 만들기
3. 각 txt 파일에 정확히 2줄 작성 (UTF-8, BOM 없음)

## 폰트 매핑 확인

`make_screenshots.py` 의 `LANG_TO_FONT` 딕셔너리에 사용할 모든 언어 코드가 매핑되어 있어야 합니다.

매핑 예시:
```python
LANG_TO_FONT = {
    "en": "NotoSans-Black.ttf",
    "ko": "NotoSansKR-Black.ttf",
    "ja": "NotoSansJP-Black.ttf",
    # ...
}
```

매핑되지 않은 언어 코드는 합성 시 skip됩니다.

## 영어/한국어 빠뜨리지 마세요

자동화 작업 중 본진 언어를 까먹는 흔한 실수가 있습니다. 출시 언어 리스트에 ko, en이 포함되어야 한다면 반드시 폴더로 만들어 두세요.

Claude 작업 시 이 부분도 함께 체크합니다.
