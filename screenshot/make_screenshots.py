"""
Palette - App Store Screenshot Generator (v3)

Renders multi-language App Store screenshots by composing translated text
onto pre-designed mockup PNGs.

Usage:
    python make_screenshots.py              # Process all languages in output/
    python make_screenshots.py --lang 1_en  # Process specific language only

Requirements:
    - fonts/                   : ttf files (Black weight recommended)
    - ingredient/              : 6 mockup PNGs (iphone_1~3, ipad_1~3)
    - output/{N}_{lang}/       : Text files (each with 2 lines)
    - LANG_TO_FONT mapping     : Configured below

Output:
    - screenshots/{N}_{lang}/  : Generated PNGs
    - screenshots/skipped.log  : Skip reasons
    - screenshots/render_summary.csv : Per-file font size and line count

Policy v3 (validated at 100% success on 50-language Palette project):
    - Safe Zone:  iPhone margin 100/200, iPad margin 200/200
    - Font sizes: iPhone 130 -> 50, iPad 180 -> 50, step 5pt
    - Shadow:     #1A1A1A, offset (4, 4), opacity 35%, blur 20
    - Auto line-break when font hits FONT_MIN
"""

import argparse
import csv
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ============================================================================
# Configuration
# ============================================================================

# Canvas dimensions (App Store requirements)
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

# Font sizing policy
IPHONE_FONT_START = 130
IPAD_FONT_START = 180
FONT_MIN = 50
FONT_STEP = 5

# Line spacing
LINE_HEIGHT_RATIO = 1.3

# Shadow settings
SHADOW = {
    "color": (26, 26, 26),       # #1A1A1A
    "offset_x": 4,
    "offset_y": 4,
    "opacity": 0.35,             # 35%
    "blur": 20,
}

# RTL languages (require bidi + reshape processing)
RTL_LANGS = {"ar", "ur", "he"}

# Language code -> font file mapping
# Customize this for each project's required languages.
LANG_TO_FONT = {
    # Latin / European / Cyrillic / Greek (covered by NotoSans)
    "en": "NotoSans-Black.ttf",
    "en_US": "NotoSans-Black.ttf",
    "en_GB": "NotoSans-Black.ttf",
    "en_AU": "NotoSans-Black.ttf",
    "en_CA": "NotoSans-Black.ttf",
    "de": "NotoSans-Black.ttf",
    "de_DE": "NotoSans-Black.ttf",
    "fr": "NotoSans-Black.ttf",
    "fr_FR": "NotoSans-Black.ttf",
    "fr_CA": "NotoSans-Black.ttf",
    "es": "NotoSans-Black.ttf",
    "es_ES": "NotoSans-Black.ttf",
    "es_MX": "NotoSans-Black.ttf",
    "it": "NotoSans-Black.ttf",
    "nl": "NotoSans-Black.ttf",
    "pt": "NotoSans-Black.ttf",
    "pt_BR": "NotoSans-Black.ttf",
    "pt_PT": "NotoSans-Black.ttf",
    "pl": "NotoSans-Black.ttf",
    "cs": "NotoSans-Black.ttf",
    "sk": "NotoSans-Black.ttf",
    "sl": "NotoSans-Black.ttf",
    "hr": "NotoSans-Black.ttf",
    "hu": "NotoSans-Black.ttf",
    "ro": "NotoSans-Black.ttf",
    "da": "NotoSans-Black.ttf",
    "no": "NotoSans-Black.ttf",
    "nb": "NotoSans-Black.ttf",
    "sv": "NotoSans-Black.ttf",
    "fi": "NotoSans-Black.ttf",
    "ca": "NotoSans-Black.ttf",
    "tr": "NotoSans-Black.ttf",
    "vi": "NotoSans-Black.ttf",
    "id": "NotoSans-Black.ttf",
    "ms": "NotoSans-Black.ttf",
    "ru": "NotoSans-Black.ttf",
    "uk": "NotoSans-Black.ttf",
    "bg": "NotoSans-Black.ttf",
    "el": "NotoSans-Black.ttf",

    # CJK
    "ko": "NotoSansKR-Black.ttf",
    "ja": "NotoSansJP-Black.ttf",
    "zh_Hans": "NotoSansSC-Black.ttf",
    "zh_Hant": "NotoSansTC-Black.ttf",

    # Middle East
    "ar": "NotoSansArabic-Black.ttf",
    "ur": "NotoSansArabic-Black.ttf",
    "he": "NotoSansHebrew-Black.ttf",

    # Southeast Asia
    "th": "NotoSansThai-Black.ttf",

    # South Asian
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

    # Caucasian
    "ka": "NotoSansGeorgian-Black.ttf",
}

# Path constants
ROOT = Path(__file__).parent
FONTS_DIR = ROOT / "fonts"
INGREDIENT_DIR = ROOT / "ingredient"
OUTPUT_DIR = ROOT / "output"
SCREENSHOTS_DIR = ROOT / "screenshots"

# ============================================================================
# Utility Functions
# ============================================================================

def discover_languages():
    """Scan output/ folder and return sorted list of language folders."""
    if not OUTPUT_DIR.exists():
        return []
    return sorted(
        [d.name for d in OUTPUT_DIR.iterdir() if d.is_dir()],
        key=lambda x: int(x.split("_")[0]) if x.split("_")[0].isdigit() else 9999,
    )


def parse_lang_code(folder_name):
    """Extract language code from folder name. e.g. '15_es_MX' -> 'es_MX'."""
    parts = folder_name.split("_", 1)
    if len(parts) < 2:
        return folder_name
    return parts[1]


def read_text_file(path):
    """Read 2 lines from a text file (UTF-8)."""
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\n\r") for line in f.readlines() if line.strip()]
    if len(lines) != 2:
        raise ValueError(f"Expected 2 lines, got {len(lines)} in {path}")
    return lines[0], lines[1]


def prepare_text(text, lang):
    """Apply RTL processing if needed."""
    if lang in RTL_LANGS:
        try:
            if lang in {"ar", "ur"}:
                import arabic_reshaper
                text = arabic_reshaper.reshape(text)
            from bidi.algorithm import get_display
            text = get_display(text)
        except ImportError:
            print(
                "[WARN] python-bidi or arabic-reshaper not installed. "
                "RTL text may render incorrectly.",
                file=sys.stderr,
            )
    return text


def measure_text_width(draw, text, font):
    """Measure rendered width of text in pixels."""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def measure_text_height(draw, text, font):
    """Measure rendered height of text in pixels."""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[3] - bbox[1]


def split_text_at_word_boundary(text, lang):
    """Split text into two roughly equal parts at word boundary.

    For CJK (no spaces), split at character midpoint.
    For others, split at word boundary closest to midpoint.
    """
    if lang in {"ja", "zh_Hans", "zh_Hant"}:
        mid = len(text) // 2
        return text[:mid].strip(), text[mid:].strip()

    words = text.split()
    if len(words) < 2:
        # Cannot split (single word) - return as-is and let caller handle
        return text, ""

    # Find split point closest to midpoint (by character count)
    target = len(text) // 2
    best_split = 1
    best_diff = float("inf")
    for i in range(1, len(words)):
        left = " ".join(words[:i])
        diff = abs(len(left) - target)
        if diff < best_diff:
            best_diff = diff
            best_split = i

    part1 = " ".join(words[:best_split])
    part2 = " ".join(words[best_split:])
    return part1, part2


def find_fitting_font_size(draw, lines, font_path, max_size, min_size, max_width):
    """Find the largest font size where all lines fit within max_width."""
    size = max_size
    while size >= min_size:
        font = ImageFont.truetype(str(font_path), size)
        widths = [measure_text_width(draw, line, font) for line in lines]
        if max(widths) <= max_width:
            return size, font
        size -= FONT_STEP
    return None, None


def try_with_line_break(lines, lang, font_path, min_size, max_width):
    """Try splitting long lines and check if all parts fit at min_size."""
    font = ImageFont.truetype(str(font_path), min_size)
    img = Image.new("RGB", (10, 10))
    draw = ImageDraw.Draw(img)

    new_lines = []
    for line in lines:
        if measure_text_width(draw, line, font) <= max_width:
            new_lines.append(line)
        else:
            part1, part2 = split_text_at_word_boundary(line, lang)
            if not part2:
                # Cannot split - fail
                return None
            w1 = measure_text_width(draw, part1, font)
            w2 = measure_text_width(draw, part2, font)
            if w1 > max_width or w2 > max_width:
                return None
            new_lines.append(part1)
            new_lines.append(part2)

    return new_lines

# ============================================================================
# Rendering
# ============================================================================

def render_screenshot(mockup_path, lines, lang, font_path, device_config, output_path):
    """Render a single screenshot.

    Returns:
        dict with 'success', 'font_size', 'line_count', 'reason' keys.
    """
    base = Image.open(mockup_path).convert("RGBA")
    canvas_w, canvas_h = device_config["canvas"]

    # Verify canvas size matches expectations
    if base.size != (canvas_w, canvas_h):
        return {
            "success": False,
            "font_size": 0,
            "line_count": 0,
            "reason": f"Mockup size {base.size} != expected {(canvas_w, canvas_h)}",
        }

    safe = device_config["safe_zone"]
    max_width = safe["width"]
    max_height = safe["height"]
    center_x = (safe["x_min"] + safe["x_max"]) // 2
    center_y = (safe["y_min"] + safe["y_max"]) // 2

    # Determine starting font size
    if device_config is IPHONE:
        font_start = IPHONE_FONT_START
    else:
        font_start = IPAD_FONT_START

    # Apply RTL processing
    processed_lines = [prepare_text(line, lang) for line in lines]

    # Find largest font size that fits
    img = Image.new("RGB", (10, 10))
    draw = ImageDraw.Draw(img)
    font_size, font = find_fitting_font_size(
        draw, processed_lines, font_path, font_start, FONT_MIN, max_width
    )

    final_lines = processed_lines

    # If smallest font doesn't fit, try line-break
    if font_size is None:
        broken = try_with_line_break(processed_lines, lang, font_path, FONT_MIN, max_width)
        if broken is None:
            return {
                "success": False,
                "font_size": 0,
                "line_count": 0,
                "reason": "Text exceeds Safe Zone width even at FONT_MIN with line-break",
            }
        final_lines = broken
        font_size = FONT_MIN
        font = ImageFont.truetype(str(font_path), FONT_MIN)

    # Verify total height fits
    line_height = int(font_size * LINE_HEIGHT_RATIO)
    total_height = line_height * len(final_lines)
    if total_height > max_height:
        return {
            "success": False,
            "font_size": font_size,
            "line_count": len(final_lines),
            "reason": f"Text height {total_height} exceeds Safe Zone height {max_height}",
        }

    # Render shadow layer
    shadow_layer = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)

    shadow_color = SHADOW["color"] + (int(255 * SHADOW["opacity"]),)
    start_y = center_y - total_height // 2 + (line_height - font_size) // 2

    for i, line in enumerate(final_lines):
        line_w = measure_text_width(shadow_draw, line, font)
        line_x = center_x - line_w // 2
        line_y = start_y + i * line_height
        shadow_draw.text(
            (line_x + SHADOW["offset_x"], line_y + SHADOW["offset_y"]),
            line,
            font=font,
            fill=shadow_color,
        )

    # Apply Gaussian blur to shadow
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(SHADOW["blur"]))

    # Composite shadow onto base
    base.alpha_composite(shadow_layer)

    # Render sharp white text on top
    draw = ImageDraw.Draw(base)
    for i, line in enumerate(final_lines):
        line_w = measure_text_width(draw, line, font)
        line_x = center_x - line_w // 2
        line_y = start_y + i * line_height
        draw.text((line_x, line_y), line, font=font, fill=(255, 255, 255, 255))

    # Convert to RGB and save
    final = base.convert("RGB")

    # Final size check
    if final.size != (canvas_w, canvas_h):
        return {
            "success": False,
            "font_size": font_size,
            "line_count": len(final_lines),
            "reason": f"Final size {final.size} != expected {(canvas_w, canvas_h)}",
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    final.save(output_path, format="PNG", optimize=False)

    return {
        "success": True,
        "font_size": font_size,
        "line_count": len(final_lines),
        "reason": None,
    }

# ============================================================================
# Main
# ============================================================================

def process_language(lang_folder):
    """Process all 6 screenshots for one language."""
    lang_code = parse_lang_code(lang_folder)
    folder_path = OUTPUT_DIR / lang_folder

    if lang_code not in LANG_TO_FONT:
        return {
            "lang": lang_folder,
            "success_count": 0,
            "skip_count": 6,
            "errors": [f"Language code '{lang_code}' not in LANG_TO_FONT"],
            "render_logs": [],
        }

    font_file = LANG_TO_FONT[lang_code]
    font_path = FONTS_DIR / font_file

    if not font_path.exists():
        return {
            "lang": lang_folder,
            "success_count": 0,
            "skip_count": 6,
            "errors": [f"Font file not found: {font_path}"],
            "render_logs": [],
        }

    success_count = 0
    skip_count = 0
    errors = []
    render_logs = []

    for slot in [1, 2, 3]:
        text_file = folder_path / f"{lang_folder}_{slot}.txt"
        if not text_file.exists():
            errors.append(f"Missing text file: {text_file.name}")
            skip_count += 2
            continue

        try:
            line1, line2 = read_text_file(text_file)
        except Exception as e:
            errors.append(f"Error reading {text_file.name}: {e}")
            skip_count += 2
            continue

        for device_name, device_config in [("iphone", IPHONE), ("ipad", IPAD)]:
            mockup_path = INGREDIENT_DIR / f"{device_name}_{slot}.png"
            if not mockup_path.exists():
                errors.append(f"Missing mockup: {mockup_path.name}")
                skip_count += 1
                continue

            output_path = SCREENSHOTS_DIR / lang_folder / f"{lang_folder}_{device_name}_{slot}.png"

            result = render_screenshot(
                mockup_path, [line1, line2], lang_code, font_path, device_config, output_path
            )

            log_entry = {
                "file": output_path.name,
                "device": device_name,
                "slot": slot,
                "success": result["success"],
                "font_size": result["font_size"],
                "line_count": result["line_count"],
                "reason": result["reason"],
            }
            render_logs.append(log_entry)

            if result["success"]:
                success_count += 1
            else:
                skip_count += 1
                errors.append(
                    f"{output_path.name}: {result['reason']}"
                )

    return {
        "lang": lang_folder,
        "success_count": success_count,
        "skip_count": skip_count,
        "errors": errors,
        "render_logs": render_logs,
    }


def main():
    parser = argparse.ArgumentParser(description="Generate App Store screenshots")
    parser.add_argument("--lang", help="Process only specified language folder (e.g., '1_en')")
    args = parser.parse_args()

    # Validate environment
    if not FONTS_DIR.exists():
        print(f"[ERROR] fonts/ directory not found at {FONTS_DIR}", file=sys.stderr)
        sys.exit(1)
    if not INGREDIENT_DIR.exists():
        print(f"[ERROR] ingredient/ directory not found at {INGREDIENT_DIR}", file=sys.stderr)
        sys.exit(1)
    if not OUTPUT_DIR.exists():
        print(f"[ERROR] output/ directory not found at {OUTPUT_DIR}", file=sys.stderr)
        sys.exit(1)

    SCREENSHOTS_DIR.mkdir(exist_ok=True)

    # Determine which languages to process
    if args.lang:
        languages = [args.lang]
    else:
        languages = discover_languages()

    if not languages:
        print("[ERROR] No language folders found in output/", file=sys.stderr)
        sys.exit(1)

    print(f"Processing {len(languages)} language(s)...")

    # Process each language
    all_results = []
    skipped_log_lines = []
    summary_rows = []

    for i, lang_folder in enumerate(languages, 1):
        result = process_language(lang_folder)
        all_results.append(result)

        iphone_ok = sum(1 for r in result["render_logs"] if r["device"] == "iphone" and r["success"])
        ipad_ok = sum(1 for r in result["render_logs"] if r["device"] == "ipad" and r["success"])
        status = "✓" if result["skip_count"] == 0 else "✗"

        print(f"[{i}/{len(languages)}] {lang_folder:20s} iphone({iphone_ok}/3) ipad({ipad_ok}/3) {status}")

        for err in result["errors"]:
            print(f"  [WARN] {err}")
            skipped_log_lines.append(f"{lang_folder}: {err}")

        for log in result["render_logs"]:
            summary_rows.append({
                "file": log["file"],
                "device": log["device"],
                "slot": log["slot"],
                "success": log["success"],
                "font_size": log["font_size"],
                "line_count": log["line_count"],
                "reason": log["reason"] or "",
            })

    # Write logs
    skipped_log_path = SCREENSHOTS_DIR / "skipped.log"
    with open(skipped_log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(skipped_log_lines))

    summary_csv_path = SCREENSHOTS_DIR / "render_summary.csv"
    with open(summary_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["file", "device", "slot", "success", "font_size", "line_count", "reason"],
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    # Final summary
    total_success = sum(r["success_count"] for r in all_results)
    total_skip = sum(r["skip_count"] for r in all_results)
    total_expected = len(languages) * 6

    print("\n" + "=" * 60)
    print(f"Total: {total_success}/{total_expected} succeeded, {total_skip} skipped")
    print(f"Logs: {skipped_log_path}")
    print(f"Summary: {summary_csv_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
