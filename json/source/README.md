# source/

영문 메타데이터 JSON 파일이 들어가는 폴더입니다.

## 파일

```
source/
└── en-US.json    ← 사용자(osk)가 작성하는 영문 ASC 메타데이터
```

## en-US.json 형식

```json
{
  "en-US": {
    "name": "App Name (30 chars max, ASO keywords)",
    "subtitle": "Subtitle (30 chars max)",
    "promotional_text": "Promotional text (170 chars max)",
    "description": "Full description (4000 chars max)\n\nMUST include EULA link at end:\nhttps://www.apple.com/legal/internet-services/itunes/dev/stdeula/",
    "keywords": "keyword1,keyword2,keyword3 (100 chars max, comma-separated, no spaces after commas)",
    "subscription_name": "Subscription name (30 chars max)",
    "subscription_display_name": "Display name (30 chars max)",
    "subscription_description": "Subscription description (1000 chars max)"
  }
}
```

## 8개 키별 한도

| 키 | 한도 | 용도 |
|---|---|---|
| `name` | 30자 | 앱 이름 (영문 ASO 키워드 강하게) |
| `subtitle` | 30자 | 부제 (검색 키워드) |
| `promotional_text` | 170자 | 프로모 (자주 업데이트 가능) |
| `description` | 4000자 | 본문 설명 (EULA 링크 포함) |
| `keywords` | 100자 | 검색 키워드 (콤마 구분, 공백 없이) |
| `subscription_name` | 30자 | 구독 상품 이름 |
| `subscription_display_name` | 30자 | 구독 표시 이름 |
| `subscription_description` | 1000자 | 구독 설명 |

## 작성 원칙

- **8개 키 모두 필수** (en-US 베이스이므로)
- **인코딩**: UTF-8 (BOM 없음)
- **JSON 유효성 필수**: 끝에 콤마 X, 따옴표 정확히
- **위험 단어 회피**: diagnose, treat, predict, guaranteed, optimal, AI, cure, prevent, heal, expert, professional
- **EULA 링크**: description 마지막 줄에 반드시 포함
  ```
  https://www.apple.com/legal/internet-services/itunes/dev/stdeula/
  ```

## Claude 작업 흐름

사용자가 `en-US.json` 작성 → Claude 가:

1. 영문 메타데이터 분석 (의도 + ASO 키워드 추출)
2. 38개 비영어 locale 로 ASO 번역
   - 직역/의역 X
   - 각 언어권 검색 키워드 중심 재구성
   - `name`, `keywords` 키는 omit (영문만 사용)
3. `json/locales.json` 자동 생성 (39국 통합)

자세한 ASO 원칙은 `../TRANSLATION_GUIDE.md` 참고.

## 주의

- **이 폴더는 입력 전용** — Claude 가 수정하지 않음
- **다른 앱 작업 시** — 이 파일 하나만 갈아끼우면 끝
- **결과물은 부모 폴더** — `json/locales.json` 에 저장됨
