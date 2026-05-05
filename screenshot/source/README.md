# source/

영문 슬로건 JSON 파일이 들어가는 폴더입니다.

## 파일

```
source/
└── en-US.json    ← 사용자가 작성하는 영문 슬로건
```

## en-US.json 형식

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

## 규칙

- **slogan_1, 2, 3**: 각각 1, 2, 3번 PNG 슬롯에 매핑
- **각 슬로건은 정확히 2줄** (배열 요소 2개)
- **인코딩**: UTF-8 (BOM 없음)
- **각 줄은 짧고 강한 ASO 키워드 권장**:
  - subtitle 30자 같은 한도 없음 (스크린샷에 들어가는 시각적 텍스트)
  - 단, 너무 길면 자동 줄바꿈 발생 → 가능하면 짧게

## Claude 작업 흐름

사용자가 `en-US.json` 작성 → Claude 가:

1. 영문 슬로건 분석 (의도 + ASO 키워드 추출)
2. N개 언어로 ASO 번역 (직역/의역 X, 검색 키워드 중심)
3. `output/{번호}_{언어}/{번호}_{언어}_{1|2|3}.txt` 자동 생성

번역 원칙은 `json/TRANSLATION_GUIDE.md` 의 ASO 가이드와 동일.

## 주의

- **이 폴더는 입력 전용** — Claude 가 수정하지 않음
- **mockup PNG 와 분리** — mockup 은 `ingredient/` 폴더
- **다른 앱 작업 시** — 이 파일 하나만 갈아끼우면 끝
