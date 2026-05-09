"""Export a built font to TTF and WOFF2."""

import os


def export_font(font, output_dir, basename):
    """Write font as <basename>.ttf and <basename>.woff2."""
    os.makedirs(output_dir, exist_ok=True)

    ttf_path = os.path.join(output_dir, f"{basename}.ttf")
    woff2_path = os.path.join(output_dir, f"{basename}.woff2")

    font.save(ttf_path)
    print(f"  Saved {ttf_path}")

    font.flavor = "woff2"
    font.save(woff2_path)
    print(f"  Saved {woff2_path}")

    font.flavor = None
