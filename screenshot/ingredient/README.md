# ingredient/

이 폴더에 **mockup PNG 6장만** 넣으세요. JSON 파일은 `source/` 폴더로 이동.

## 필요한 파일

```
ingredient/
├── iphone_1.png   (1242 x 2688)
├── iphone_2.png   (1242 x 2688)
├── iphone_3.png   (1242 x 2688)
├── ipad_1.png     (2048 x 2732)
├── ipad_2.png     (2048 x 2732)
└── ipad_3.png     (2048 x 2732)
```

## 각 PNG의 구성

각 mockup은 다음을 포함합니다:
- **배경색** (예: 노랑/주황/파랑)
- **iPhone 또는 iPad mockup** (폰 본체, 스크린샷 합성 완료)
- **상단 텍스트 영역**은 비어있음 (스크립트가 여기에 텍스트 합성)

## 픽셀 크기 절대 변경 금지

App Store는 정확한 픽셀 크기를 요구합니다:
- iPhone 6.7": **1242 x 2688**
- iPad 13": **2048 x 2732**

이 크기와 다른 PNG를 넣으면 검증에서 FAIL.

## Safe Zone 확인

`CLAUDE.md` 의 Safe Zone 좌표가 mockup의 텍스트 영역과 일치하는지 확인하세요.

기본 정책 (3차 검증 완료):
- iPhone: 좌우 100px, 위 200px, 아래 1750px (텍스트 영역 1042 x 738)
- iPad: 좌우 200px, 위 200px, 아래 1850px (텍스트 영역 1648 x 682)

mockup의 텍스트 영역이 다르면 `make_screenshots.py` 의 `IPHONE`/`IPAD` 상수를 수정해야 합니다.

## 폴더 분리 원칙

| 폴더 | 내용 |
|------|------|
| `ingredient/` | mockup PNG 6장 (이 폴더) |
| `source/` | 영문 슬로건 JSON (`en-US.json`) |
| `fonts/` | ttf 폰트 파일 |
| `output/` | 언어별 텍스트 (Claude 자동 생성) |
| `screenshots/` | 합성 결과 PNG (스크립트 자동 생성) |

→ JSON 파일은 절대 `ingredient/` 에 두지 말 것. `source/` 로.
