"""Datatype Progress configuration constants."""

from dataclasses import dataclass

FONT_VERSION = "0.2.0"

UPM = 1000
ASCENDER = 800
DESCENDER = -200
CAP_HEIGHT = 700
X_HEIGHT = 500
TYPO_ASCENDER = 1000
TYPO_DESCENDER = -300
WIN_ASCENT = 976
WIN_DESCENT = 251

ASCII_WIDTH = 500
SPACE_WIDTH = 250
DIGIT_WIDTH = 500

FAMILY_NAME = "DatatypeProgress"
REGULAR_STYLE = "Regular"

# Maximum number of stacked segments (horizontal multi-segment).
# Each segment uses palette index = position (1..MAX_SEGMENTS).
MAX_SEGMENTS = 8


@dataclass
class FontParams:
    """Per-master parameters for the bar geometry.

    wdth axis controls the long dimension; wght controls the track border thickness.
    """
    h_bar_width: int = 2400
    h_bar_height: int = 420
    h_bar_baseline: int = 60
    h_bar_border: int = 50
    h_bar_padding: int = 20
    h_bar_lead: int = 60
    h_bar_trail: int = 60

    v_bar_width: int = 460
    v_bar_height: int = 900
    v_bar_baseline: int = -150
    v_bar_border: int = 50
    v_bar_padding: int = 20
    v_bar_lead: int = 40
    v_bar_trail: int = 40

    @property
    def h_inner_width(self):
        """Inner usable area width for fills (excluding borders + padding + lead/trail)."""
        return (self.h_bar_width
                - self.h_bar_lead - self.h_bar_trail
                - 2 * self.h_bar_border
                - 2 * self.h_bar_padding)

    @property
    def h_open_advance(self):
        """Advance width of the opener glyph: lead + border + padding."""
        return self.h_bar_lead + self.h_bar_border + self.h_bar_padding

    @property
    def h_close_advance(self):
        """Advance width of the closer glyph: padding + border + trail."""
        return self.h_bar_padding + self.h_bar_border + self.h_bar_trail


# Variable font axis masters
# (wdth, wght, h_bar_width, h_bar_border, v_bar_width, v_bar_border)
AXIS_MASTERS = [
    (100, 400,  2400,  50,  460,  50),    # Default (Regular)
    ( 50, 400,  1200,  50,  230,  50),
    (150, 400,  3600,  50,  690,  50),

    (100, 100,  2400,  18,  460,  18),    # Thin
    ( 50, 100,  1200,  18,  230,  18),
    (150, 100,  3600,  18,  690,  18),

    (100, 900,  2400, 110,  460, 110),    # Black
    ( 50, 900,  1200, 110,  230, 110),
    (150, 900,  3600, 110,  690, 110),
]


def params_for_master(h_w, h_b, v_w, v_b):
    return FontParams(
        h_bar_width=h_w,
        h_bar_border=h_b,
        v_bar_width=v_w,
        v_bar_border=v_b,
    )


NAMED_INSTANCES = [
    ("Thin",       100, 100),
    ("ExtraLight", 100, 200),
    ("Light",      100, 300),
    ("Regular",    100, 400),
    ("Medium",     100, 500),
    ("SemiBold",   100, 600),
    ("Bold",       100, 700),
    ("ExtraBold",  100, 800),
    ("Black",      100, 900),
]


# CPAL palettes — each has 9 entries:
# index 0 = track color, indices 1..8 = fill colors for segment positions 1..8
PALETTES = [
    # name, [track, pos1, pos2, pos3, pos4, pos5, pos6, pos7, pos8]
    ("sequential", [
        (0xE5, 0xE7, 0xEB, 0xFF),   # 0 track  (slate-200)
        (0x10, 0xB9, 0x81, 0xFF),   # 1 emerald-500
        (0x05, 0x96, 0x69, 0xFF),   # 2 emerald-600
        (0x04, 0x78, 0x57, 0xFF),   # 3 emerald-700
        (0x06, 0x5F, 0x46, 0xFF),   # 4 emerald-800
        (0x06, 0x4E, 0x3B, 0xFF),   # 5 emerald-900
        (0x02, 0x2C, 0x22, 0xFF),   # 6 darker
        (0x01, 0x1B, 0x14, 0xFF),   # 7 deepest
        (0x00, 0x10, 0x0C, 0xFF),   # 8 near-black
    ]),
    ("rag", [
        (0xE5, 0xE7, 0xEB, 0xFF),   # 0 track
        (0x10, 0xB9, 0x81, 0xFF),   # 1 green
        (0xF5, 0x9E, 0x0B, 0xFF),   # 2 amber
        (0xEF, 0x44, 0x44, 0xFF),   # 3 red
        (0x6B, 0x72, 0x80, 0xFF),   # 4 gray fallback
        (0x6B, 0x72, 0x80, 0xFF),   # 5
        (0x6B, 0x72, 0x80, 0xFF),   # 6
        (0x6B, 0x72, 0x80, 0xFF),   # 7
        (0x6B, 0x72, 0x80, 0xFF),   # 8
    ]),
    ("categorical", [
        (0xE5, 0xE7, 0xEB, 0xFF),   # 0 track
        (0x3B, 0x82, 0xF6, 0xFF),   # 1 blue
        (0x10, 0xB9, 0x81, 0xFF),   # 2 emerald
        (0xF5, 0x9E, 0x0B, 0xFF),   # 3 amber
        (0xEF, 0x44, 0x44, 0xFF),   # 4 red
        (0x8B, 0x5C, 0xF6, 0xFF),   # 5 violet
        (0x06, 0xB6, 0xD4, 0xFF),   # 6 cyan
        (0xEC, 0x48, 0x99, 0xFF),   # 7 pink
        (0x84, 0xCC, 0x16, 0xFF),   # 8 lime
    ]),
    ("ocean", [
        (0xE5, 0xE7, 0xEB, 0xFF),   # 0 track
        (0xDB, 0xEA, 0xFE, 0xFF),   # 1 blue-100
        (0xBF, 0xDB, 0xFE, 0xFF),   # 2 blue-200
        (0x93, 0xC5, 0xFD, 0xFF),   # 3 blue-300
        (0x60, 0xA5, 0xFA, 0xFF),   # 4 blue-400
        (0x3B, 0x82, 0xF6, 0xFF),   # 5 blue-500
        (0x25, 0x63, 0xEB, 0xFF),   # 6 blue-600
        (0x1D, 0x4E, 0xD8, 0xFF),   # 7 blue-700
        (0x1E, 0x40, 0xAF, 0xFF),   # 8 blue-800
    ]),
    ("mono", [
        (0xE5, 0xE7, 0xEB, 0xFF),   # 0 track
        (0x1F, 0x29, 0x37, 0xFF),   # 1..8 all neutral dark
        (0x1F, 0x29, 0x37, 0xFF),
        (0x1F, 0x29, 0x37, 0xFF),
        (0x1F, 0x29, 0x37, 0xFF),
        (0x1F, 0x29, 0x37, 0xFF),
        (0x1F, 0x29, 0x37, 0xFF),
        (0x1F, 0x29, 0x37, 0xFF),
        (0x1F, 0x29, 0x37, 0xFF),
    ]),
]
