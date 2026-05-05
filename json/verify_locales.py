"""Verify locales.json per TRANSLATION_GUIDE.md."""

import json
import sys
from pathlib import Path


# 39 locale (ASC 표준 hyphen)
EXPECTED_LOCALES = {
    "en-US", "ko", "ja", "zh-Hans", "zh-Hant", "es", "es-MX", "fr", "fr-CA",
    "de-DE", "it", "pt-BR", "pt-PT", "nl", "pl", "sv", "da", "nb", "fi", "cs",
    "hu", "ru", "ro", "sk", "uk", "hr", "bg", "el", "ca", "en-GB",
    "ar", "he", "hi", "th", "vi", "id", "ms", "tr", "ka",
}

# 글자수 한도 (Apple ASC)
LIMITS = {
    "name": 30,
    "subtitle": 30,
    "promotional_text": 170,
    "description": 4000,
    "keywords": 100,
    "subscription_name": 30,
    "subscription_display_name": 30,
    "subscription_description": 1000,
}

# en-US 필수 키 (8개)
EN_US_REQUIRED = set(LIMITS.keys())

# 비영어 locale 필수 키 (6개, name/keywords omit)
NON_EN_REQUIRED = EN_US_REQUIRED - {"name", "keywords"}

# 위험 단어 (영문 기준)
RISKY_WORDS = [
    "diagnose", "diagnoses", "treat", "treats", "treatment",
    "predict", "predicts", "prediction",
    "guaranteed", "guarantee",
    "optimal", "optimum",
    " AI ", "AI-powered", "AI-based",
    "cure", "cures",
    "prevent", "prevents", "prevention",
    "heal", "heals",
]


def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_locales.py <locales.json>", file=sys.stderr)
        sys.exit(2)

    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"[FATAL] {path} 파일 없음", file=sys.stderr)
        sys.exit(2)

    print("=" * 64)
    print(f"[검증 시작] {path}")
    print("=" * 64)

    # 1. JSON 유효성
    print()
    print("[검증 1] JSON 유효성")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print("  ✓ JSON 파싱 성공")
    except json.JSONDecodeError as e:
        print(f"  ✗ JSON 파싱 실패: {e}")
        sys.exit(1)

    # 2. locale 키 개수
    print()
    print("[검증 2] locale 키 개수")
    actual_locales = set(data.keys())
    missing = EXPECTED_LOCALES - actual_locales
    extra = actual_locales - EXPECTED_LOCALES
    print(f"  기대: {len(EXPECTED_LOCALES)}개")
    print(f"  실제: {len(actual_locales)}개")
    if missing:
        print(f"  ✗ 누락 {len(missing)}: {sorted(missing)}")
    if extra:
        print(f"  ⚠ 추가 {len(extra)}: {sorted(extra)} (ASC 표준 외)")
    if not missing and not extra:
        print(f"  ✓ 39개 locale 모두 일치")

    # 3. en-US 필수 키
    print()
    print("[검증 3] en-US 필수 키 (8개)")
    if "en-US" not in data:
        print("  ✗ en-US 키 자체 없음")
        sys.exit(1)
    en_keys = set(data["en-US"].keys())
    en_missing = EN_US_REQUIRED - en_keys
    if en_missing:
        print(f"  ✗ en-US 누락 키: {sorted(en_missing)}")
    else:
        print(f"  ✓ 8/8 키 모두 존재")

    # 4. 비영어 locale 필수 키
    print()
    print("[검증 4] 비영어 locale 필수 키 (6개)")
    locale_key_violations = []
    for locale, fields in data.items():
        if locale == "en-US":
            continue
        keys = set(fields.keys())
        miss = NON_EN_REQUIRED - keys
        forbidden = keys & {"name", "keywords"}
        if miss:
            locale_key_violations.append((locale, "missing", sorted(miss)))
        if forbidden:
            locale_key_violations.append((locale, "should_omit", sorted(forbidden)))
    if locale_key_violations:
        print(f"  ✗ 비영어 locale 키 위반 {len(locale_key_violations)}개:")
        for locale, kind, keys in locale_key_violations[:10]:
            print(f"    - {locale} ({kind}): {keys}")
    else:
        print(f"  ✓ 모든 비영어 locale 6개 키 보유, name/keywords omit")

    # 5. 글자수 한도
    print()
    print("[검증 5] 글자수 한도")
    over_limits = []
    for locale, fields in data.items():
        for key, value in fields.items():
            limit = LIMITS.get(key)
            if limit and isinstance(value, str) and len(value) > limit:
                over_limits.append((locale, key, len(value), limit))
    if over_limits:
        print(f"  ✗ 한도 초과 {len(over_limits)}개:")
        for locale, key, actual, limit in over_limits[:20]:
            print(f"    - {locale}.{key}: {actual}/{limit} 자")
    else:
        print(f"  ✓ 모든 텍스트 한도 내")

    # 6. 위험 단어 (영문)
    print()
    print("[검증 6] 위험 단어 (영문 baseline)")
    risky_hits = []
    if "en-US" in data:
        en_text = " ".join(
            v for k, v in data["en-US"].items()
            if isinstance(v, str)
        ).lower()
        for word in RISKY_WORDS:
            if word.strip().lower() in en_text:
                risky_hits.append(word.strip())
    if risky_hits:
        print(f"  ⚠ en-US 에 위험 단어 {len(risky_hits)}개 검출:")
        for w in risky_hits:
            print(f"    - {w}")
        print("  → TRANSLATION_GUIDE.md 의 대체 표현 참고")
    else:
        print(f"  ✓ en-US 위험 단어 0건")

    # 요약
    print()
    print("=" * 64)
    print("[검증 요약]")
    print("=" * 64)
    fails = (
        len(missing)
        + len(locale_key_violations)
        + len(over_limits)
    )
    print(f"- locale 누락: {len(missing)}")
    print(f"- 비영어 키 위반: {len(locale_key_violations)}")
    print(f"- 글자수 초과: {len(over_limits)}")
    print(f"- 위험 단어: {len(risky_hits)} (warning, fail 처리 X)")
    print()
    if fails == 0:
        print("[전체 결과]: PASS")
        print("=" * 64)
        sys.exit(0)
    else:
        print("[전체 결과]: FAIL")
        print("=" * 64)
        sys.exit(1)


if __name__ == "__main__":
    main()
