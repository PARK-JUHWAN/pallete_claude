"""
Palette - Screenshot Verification

Verifies that all generated PNGs match App Store specifications:
- File existence
- PNG format
- Pixel dimensions (iPhone 1242x2688, iPad 2048x2732)
- File size (not 0 bytes)
- Color mode (RGB/RGBA)
- Skip log review

Auto-detects expected language count by scanning output/ folder.
"""

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).parent
OUTPUT_DIR = ROOT / "output"
SCREENSHOTS_DIR = ROOT / "screenshots"

EXPECTED_IPHONE_SIZE = (1242, 2688)
EXPECTED_IPAD_SIZE = (2048, 2732)

MIN_FILE_SIZE_KB = 50  # Files smaller than this are suspicious


def discover_languages():
    """Get sorted list of language folders from output/."""
    if not OUTPUT_DIR.exists():
        return []
    return sorted(
        [d.name for d in OUTPUT_DIR.iterdir() if d.is_dir()],
        key=lambda x: int(x.split("_")[0]) if x.split("_")[0].isdigit() else 9999,
    )


def expected_files_for_lang(lang_folder):
    """Return list of expected PNG filenames for one language."""
    files = []
    for slot in [1, 2, 3]:
        files.append(f"{lang_folder}_iphone_{slot}.png")
        files.append(f"{lang_folder}_ipad_{slot}.png")
    return files


def is_valid_png(file_path):
    """Check if file is a valid PNG by reading magic bytes."""
    try:
        with open(file_path, "rb") as f:
            magic = f.read(8)
        return magic == b"\x89PNG\r\n\x1a\n"
    except Exception:
        return False


def main():
    if not SCREENSHOTS_DIR.exists():
        print(f"[ERROR] screenshots/ directory not found at {SCREENSHOTS_DIR}", file=sys.stderr)
        sys.exit(1)

    languages = discover_languages()
    if not languages:
        print("[ERROR] No language folders found in output/", file=sys.stderr)
        sys.exit(1)

    expected_total = len(languages) * 6

    print("=" * 64)
    print(f"[Verification Started] {len(languages)} languages, {expected_total} files expected")
    print("=" * 64)

    # Tracking
    missing_files = []
    invalid_format = []
    wrong_size = []
    too_small = []
    wrong_mode = []
    skipped_files = []

    valid_count = 0

    # Check 1-5
    for lang_folder in languages:
        screenshot_folder = SCREENSHOTS_DIR / lang_folder
        if not screenshot_folder.exists():
            for fname in expected_files_for_lang(lang_folder):
                missing_files.append(f"{lang_folder}/{fname}")
            continue

        for fname in expected_files_for_lang(lang_folder):
            fpath = screenshot_folder / fname
            if not fpath.exists():
                missing_files.append(f"{lang_folder}/{fname}")
                continue

            # Check 2: PNG format
            if not is_valid_png(fpath):
                invalid_format.append(f"{lang_folder}/{fname}")
                continue

            # Check 4: File size
            file_size_kb = fpath.stat().st_size / 1024
            if file_size_kb < MIN_FILE_SIZE_KB:
                too_small.append(f"{lang_folder}/{fname} ({file_size_kb:.1f} KB)")
                continue

            # Check 3: Pixel dimensions
            try:
                with Image.open(fpath) as img:
                    actual_size = img.size
                    actual_mode = img.mode
            except Exception as e:
                invalid_format.append(f"{lang_folder}/{fname} (read error: {e})")
                continue

            expected_size = EXPECTED_IPHONE_SIZE if "iphone" in fname else EXPECTED_IPAD_SIZE
            if actual_size != expected_size:
                wrong_size.append(
                    f"{lang_folder}/{fname} (got {actual_size}, expected {expected_size})"
                )
                continue

            # Check 5: Color mode
            if actual_mode not in ("RGB", "RGBA"):
                wrong_mode.append(f"{lang_folder}/{fname} (mode: {actual_mode})")
                continue

            valid_count += 1

    # Check 6: Skip log
    skipped_log = SCREENSHOTS_DIR / "skipped.log"
    if skipped_log.exists():
        with open(skipped_log, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if content:
            skipped_files = [line for line in content.split("\n") if line.strip()]

    # Print report
    print()
    print("[Check 1] File Existence")
    if missing_files:
        print(f"  ✗ {len(missing_files)} missing files")
        for f in missing_files[:10]:
            print(f"    - {f}")
        if len(missing_files) > 10:
            print(f"    ... and {len(missing_files) - 10} more")
    else:
        print(f"  ✓ All {expected_total} files present")

    print()
    print("[Check 2] PNG Format")
    if invalid_format:
        print(f"  ✗ {len(invalid_format)} invalid/corrupted PNG files")
        for f in invalid_format[:10]:
            print(f"    - {f}")
    else:
        print(f"  ✓ All files are valid PNG")

    print()
    print("[Check 3] Pixel Dimensions")
    if wrong_size:
        print(f"  ✗ {len(wrong_size)} files with incorrect dimensions")
        for f in wrong_size[:10]:
            print(f"    - {f}")
    else:
        print(f"  ✓ All dimensions correct (iPhone 1242x2688, iPad 2048x2732)")

    print()
    print("[Check 4] File Size")
    if too_small:
        print(f"  ✗ {len(too_small)} suspiciously small files")
        for f in too_small[:10]:
            print(f"    - {f}")
    else:
        print(f"  ✓ No suspicious files")

    print()
    print("[Check 5] Color Mode")
    if wrong_mode:
        print(f"  ✗ {len(wrong_mode)} files with wrong color mode")
        for f in wrong_mode[:10]:
            print(f"    - {f}")
    else:
        print(f"  ✓ All files use RGB/RGBA")

    print()
    print("[Check 6] Skip Log")
    if skipped_files:
        print(f"  ✗ {len(skipped_files)} files were skipped during rendering")
        for s in skipped_files[:10]:
            print(f"    - {s}")
        if len(skipped_files) > 10:
            print(f"    ... and {len(skipped_files) - 10} more (see skipped.log)")
    else:
        print(f"  ✓ No skips during rendering")

    # Summary
    total_problems = (
        len(missing_files)
        + len(invalid_format)
        + len(wrong_size)
        + len(too_small)
        + len(wrong_mode)
        + len(skipped_files)
    )

    print()
    print("=" * 64)
    print("[Verification Summary]")
    print("=" * 64)
    print(f"Expected files:   {expected_total}")
    print(f"Valid files:      {valid_count}")
    print(f"Total problems:   {total_problems}")
    print()
    if total_problems == 0:
        print("[Result]: PASS")
        sys.exit(0)
    else:
        print("[Result]: FAIL")
        sys.exit(1)


if __name__ == "__main__":
    main()
