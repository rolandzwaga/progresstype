"""Render specimen examples directly from the font as SVG.

Useful when a browser isn't handy — produces a self-contained SVG file showing
how each example shapes through the font, with COLR/CPAL colors honored.

Usage:
    .venv/bin/python dev/render_specimen.py [output.svg]
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen


FONT_PATH = os.path.join(
    PROJECT_ROOT, "fonts", "variable", "DatatypeProgress[wdth,wght].ttf"
)
DEFAULT_OUT = os.path.join(PROJECT_ROOT, "dev", "specimen.svg")

# For padded segments, override the trailing position to "none" so its fill
# layer doesn't paint — only the strip + border outline shows. Matches how
# the empty portion of single-segment {h:NN} looks against the page background.
TRACK_NONE = "none"

# Each example: (label, text, palette_index, font_size_px, overrides)
# overrides maps palette index -> hex color or "none", applied on top of the base palette.
EXAMPLES = [
    ("single 23%",       "{h:23}",                    2, 28, None),
    ("single 67%",       "{h:67}",                    2, 28, None),
    ("single 91%",       "{h:91}",                    2, 28, None),
    ("2 colored + pad",  "{h:30,40,30}",              2, 28, {3: TRACK_NONE}),
    ("3 colored + pad",  "{h:25,10,15,50}",           2, 28, {4: TRACK_NONE}),
    ("4 colored + pad",  "{h:20,15,10,25,30}",        2, 28, {5: TRACK_NONE}),
    ("7 colored + pad",  "{h:10,10,10,10,10,10,10,30}", 2, 28, {8: TRACK_NONE}),
    ("RAG sums to 100",  "{h:45,30,25}",              1, 28, None),
    ("sequential",       "{h:12,12,12,12,12,12,12,12}", 0, 28, None),
    ("ocean",            "{h:12,12,12,12,12,12,12,12}", 3, 28, None),
    ("mono",             "{h:65}",                    4, 28, None),
    ("vertical row",     "{v:10}{v:25}{v:40}{v:55}{v:70}{v:85}{v:100}{v:80}{v:60}{v:45}{v:30}{v:15}", 2, 56, None),
    ("inline",           "Loading {h:75}",            2, 24, None),
]

ROW_HEIGHT = 70
LEFT_MARGIN = 20
LABEL_WIDTH = 140
TEXT_X = LEFT_MARGIN + LABEL_WIDTH + 20
PAGE_WIDTH = 980


def _palette_color(palette_entries, idx, overrides=None):
    if overrides and idx in overrides:
        return overrides[idx]
    c = palette_entries[idx]
    # uharfbuzz returns a Color with .red .green .blue .alpha as 0..255 ints
    return f"#{c.red:02x}{c.green:02x}{c.blue:02x}"


def render():
    out_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT

    with open(FONT_PATH, "rb") as f:
        font_bytes = f.read()

    blob = hb.Blob(font_bytes)
    face = hb.Face(blob)
    upem = face.upem
    hb_font = hb.Font(face)

    ft = TTFont(FONT_PATH)
    glyph_set = ft.getGlyphSet()
    cpal = ft["CPAL"]
    colr = ft["COLR"]
    color_layers = colr.ColorLayers  # {base: [LayerRecord(name, colorID), ...]}

    page_height = LEFT_MARGIN * 2 + ROW_HEIGHT * len(EXAMPLES)

    svg = []
    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{PAGE_WIDTH}" '
        f'height="{page_height}" viewBox="0 0 {PAGE_WIDTH} {page_height}" '
        f'style="background:#0b0d12;font-family:system-ui,sans-serif;">'
    )

    for i, (label, text, palette_idx, font_size, overrides) in enumerate(EXAMPLES):
        y = LEFT_MARGIN + i * ROW_HEIGHT + ROW_HEIGHT // 2

        # Shape with HarfBuzz
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(hb_font, buf, {"liga": True, "calt": True})

        scale = font_size / upem  # px-per-UPM
        palette = cpal.palettes[palette_idx]

        # Group for this row, translated to (TEXT_X, y), with y-flip for OT coords
        # We'll position the text baseline at `y + font_size * 0.3` so it visually sits centered.
        baseline_y = y + font_size * 0.3
        svg.append(
            f'<text x="{LEFT_MARGIN}" y="{baseline_y}" fill="#9ca3af" '
            f'font-size="11" font-family="ui-monospace,monospace">{label}</text>'
        )
        svg.append(
            f'<text x="{LEFT_MARGIN}" y="{baseline_y + 14}" fill="#374151" '
            f'font-size="10" font-family="ui-monospace,monospace">{_xml_escape(text)}</text>'
        )

        svg.append(
            f'<g transform="translate({TEXT_X},{baseline_y}) scale({scale},-{scale})">'
        )

        cursor_x = 0
        ft_glyph_order = ft.getGlyphOrder()
        infos = buf.glyph_infos
        positions = buf.glyph_positions

        for info, pos in zip(infos, positions):
            glyph_name = ft_glyph_order[info.codepoint]
            advance_x = pos.x_advance
            offset_x = pos.x_offset
            offset_y = pos.y_offset

            # Compute the path: if glyph is a COLR base, draw each layer with
            # the layer's palette color. Otherwise draw the glyph outline in foreground.
            if glyph_name in color_layers:
                layers = color_layers[glyph_name]
                for layer in layers:
                    color = _palette_color(palette, layer.colorID, overrides)
                    if color == "none":
                        continue   # skip painting this layer entirely
                    path = _glyph_to_svg_path(glyph_set, layer.name)
                    if path:
                        svg.append(
                            f'<g transform="translate({cursor_x + offset_x},{offset_y})">'
                            f'<path d="{path}" fill="{color}"/></g>'
                        )
            else:
                path = _glyph_to_svg_path(glyph_set, glyph_name)
                if path:
                    svg.append(
                        f'<g transform="translate({cursor_x + offset_x},{offset_y})">'
                        f'<path d="{path}" fill="#e5e7eb"/></g>'
                    )

            cursor_x += advance_x

        svg.append("</g>")

    svg.append("</svg>")

    with open(out_path, "w") as f:
        f.write("\n".join(svg))
    print(f"Wrote {out_path}")


def _glyph_to_svg_path(glyph_set, name):
    if name not in glyph_set:
        return ""
    pen = SVGPathPen(glyph_set)
    glyph_set[name].draw(pen)
    return pen.getCommands()


def _xml_escape(s):
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


if __name__ == "__main__":
    render()
