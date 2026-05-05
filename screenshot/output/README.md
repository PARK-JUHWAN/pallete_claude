# output/

이 폴더에 언어별 텍스트 파일을 넣으세요.

## 폴더/파일 구조

```
output/
├── 1_en/
│   ├── 1_en_1.txt    (1번 PNG에 들어갈 2줄)
│   ├── 1_en_2.txt    (2번 PNG에 들어갈 2줄)
│   └── 1_en_3.txt    (3번 PNG에 들어갈 2줄)
├── 2_ko/
│   ├── 2_ko_1.txt
│   ├── 2_ko_2.txt
│   └── 2_ko_3.txt
└── ... (사용할 언어 만큼)
```

## 명명 규칙

- 폴더명: `{번호}_{언어코드}`
  - 번호: 정수 (순서)
  - 언어코드: BCP-47 또는 자주 쓰는 변형 (예: `en`, `en_GB`, `zh_Hans`, `pt_BR`)
- 파일명: `{번호}_{언어코드}_{1|2|3}.txt`

언어 코드의 underscore는 그대로 유지: `es_MX`, `pt_BR`, `zh_Hans`, `en_GB`

## 텍스트 파일 형식

- **인코딩**: UTF-8 (BOM 없음)
- **줄 수**: 정확히 2줄
- **빈 줄 없음**: 파일 시작/끝에 공백 없음
- **각 줄**: 한 PNG에 한 줄로 표시됨

예시 (`output/1_en/1_en_1.txt`):
```
Stop pulling all-nighters every month
Build schedules automatically
```

→ 1번 PNG (iPhone, iPad) 에 위 2줄이 한 화면에 표시됨.

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
