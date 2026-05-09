"""Horizontal progress bar glyphs and ligature feature code.

Architecture: opener + segments + closer, decomposed via GSUB.

Glyphs created (per orientation, parameterized by FontParams):

Drawing sub-glyphs (used as COLR layers, palette index 0 = track color):
  - prog_h_open_track   — left border + opener portion of top/bottom strips
  - prog_h_close_track  — right border + closer portion
  - prog_h_strip_NN     — top + bottom strips of width = NN% of inner_width  (101 glyphs)
  - prog_h_fill_NN      — colored fill rectangle of width = NN%               (101 glyphs)

Composite COLR base glyphs (these are what the cmap/GSUB outputs):
  - prog_h_open         — layers: [(prog_h_open_track, 0)]
  - prog_h_close        — layers: [(prog_h_close_track, 0)]
  - prog_h_seg_NN_posK  — layers: [(prog_h_strip_NN, 0), (prog_h_fill_NN, K)]
                          for NN ∈ 0..100 and K ∈ 1..MAX_SEGMENTS  (808 glyphs at 8 positions)

Marker glyphs (zero-width intermediate, never rendered):
  - prog_h_sep, prog_h_d0..d9

GSUB pipeline (in calt):
  1. open ligature: { h : → prog_h_open
  2. propagate: digits → prog_h_dN, comma → prog_h_sep
  3. position-1 chain: prog_h_open + digits → seg_NN_pos1   (1/2/3-digit variants)
  4. position-2 chain: seg_pos1 sep + digits → seg_NN_pos2
  5. ... up to MAX_SEGMENTS
  6. close: } in bar context → prog_h_close
"""

from sources.config import FontParams, MAX_SEGMENTS


def _rect(pen, x0, y0, x1, y1):
    pen.moveTo((x0, y0))
    pen.lineTo((x1, y0))
    pen.lineTo((x1, y1))
    pen.lineTo((x0, y1))
    pen.closePath()


def _y_bounds(p):
    """Inner-area y-bounds for the fill (between top and bottom borders)."""
    y_outer_bottom = p.h_bar_baseline
    y_outer_top = p.h_bar_baseline + p.h_bar_height
    y_inner_bottom = y_outer_bottom + p.h_bar_border + p.h_bar_padding
    y_inner_top = y_outer_top - p.h_bar_border - p.h_bar_padding
    return y_outer_bottom, y_outer_top, y_inner_bottom, y_inner_top


def _seg_advance(p, pct):
    """Advance width contributed by a segment of NN% — proportional slice of inner width."""
    if pct <= 0:
        return 0
    return max(1, round(p.h_inner_width * pct / 100))


# Segments extend their drawing this many UPM past their advance width so the
# next glyph's left edge fully covers the AA seam — eliminates sub-pixel gaps
# at small rendered sizes. Whatever follows (next segment or the closer) draws
# over this overlap region.
_SEG_OVERLAP = 8


# ---------------------------------------------------------------------------
# Drawing functions
# ---------------------------------------------------------------------------

def _draw_open_track(pen, p):
    """Opener track drawing: left vertical border + opener-width top/bottom strips.

    The left vertical border is extended right by _SEG_OVERLAP so the first
    segment's drawing overdraws any AA seam at the opener-segment boundary.
    """
    yob, yot, yib, yit = _y_bounds(p)

    # Left vertical border, extended right by overlap.
    lx0 = p.h_bar_lead
    lx1 = p.h_bar_lead + p.h_bar_border + _SEG_OVERLAP
    _rect(pen, lx0, yob, lx1, yot)

    # Top/bottom strip portions for any padding region (zero when padding=0).
    sx0 = p.h_bar_lead + p.h_bar_border
    sx1 = p.h_open_advance + _SEG_OVERLAP
    if sx1 > sx0:
        _rect(pen, sx0, yit, sx1, yot)  # top strip
        _rect(pen, sx0, yob, sx1, yib)  # bottom strip


def _draw_close_track(pen, p):
    """Closer track drawing: closer-width top/bottom strips + right vertical border."""
    yob, yot, yib, yit = _y_bounds(p)

    # The closer's local x-coordinates run from 0 to h_close_advance
    # Top + bottom strips from x=0 to x=padding+border
    strip_end = p.h_bar_padding + p.h_bar_border
    if strip_end > 0:
        _rect(pen, 0, yit, strip_end, yot)
        _rect(pen, 0, yob, strip_end, yib)

    # Right vertical border at x=padding..padding+border
    rx0 = p.h_bar_padding
    rx1 = p.h_bar_padding + p.h_bar_border
    _rect(pen, rx0, yob, rx1, yot)


def _draw_strip(pen, p, pct):
    """Top + bottom track strips spanning a segment of width = NN%, with overlap."""
    if pct <= 0:
        return
    yob, yot, yib, yit = _y_bounds(p)
    w = _seg_advance(p, pct) + _SEG_OVERLAP
    _rect(pen, 0, yit, w, yot)  # top
    _rect(pen, 0, yob, w, yib)  # bottom


def _draw_fill(pen, p, pct):
    """Colored fill rectangle for segment of width = NN%, with overlap."""
    if pct <= 0:
        return
    yob, yot, yib, yit = _y_bounds(p)
    w = _seg_advance(p, pct) + _SEG_OVERLAP
    _rect(pen, 0, yib, w, yit)


def _draw_open_base(pen, p):
    """Monochrome fallback for opener (no COLR support): full track drawing."""
    _draw_open_track(pen, p)


def _draw_close_base(pen, p):
    _draw_close_track(pen, p)


def _draw_seg_base(pen, p, pct):
    """Monochrome fallback for segment: strips + fill in foreground color."""
    _draw_strip(pen, p, pct)
    _draw_fill(pen, p, pct)


# ---------------------------------------------------------------------------
# Full-width single-segment glyphs (used by the {h:NN} direct ligature)
#
# These bake the full bar (left border + inner area + right border + lead/trail
# whitespace) into a single composite glyph with two COLR layers:
#   layer 0: prog_h_full_track   — full track frame at palette[0]
#   layer 1: prog_h_full_fill_NN — colored fill of NN% width on the left, at palette[1]
# ---------------------------------------------------------------------------

def _full_inner_x(p):
    """Return (x_inner_start, x_inner_end) within the full bar coordinate space."""
    x0 = p.h_bar_lead + p.h_bar_border + p.h_bar_padding
    x1 = p.h_bar_width - p.h_bar_trail - p.h_bar_border - p.h_bar_padding
    return x0, x1


def _draw_full_track(pen, p):
    """Full-width track frame: left border, top + bottom strips, right border."""
    yob, yot, yib, yit = _y_bounds(p)

    # Left vertical border
    lx0 = p.h_bar_lead
    lx1 = p.h_bar_lead + p.h_bar_border
    _rect(pen, lx0, yob, lx1, yot)

    # Right vertical border
    rx0 = p.h_bar_width - p.h_bar_trail - p.h_bar_border
    rx1 = p.h_bar_width - p.h_bar_trail
    _rect(pen, rx0, yob, rx1, yot)

    # Top strip + bottom strip across the full inner span (between the borders)
    sx0 = lx1
    sx1 = rx0
    if sx1 > sx0:
        _rect(pen, sx0, yit, sx1, yot)  # top
        _rect(pen, sx0, yob, sx1, yib)  # bottom


def _draw_full_fill(pen, p, pct):
    """Colored fill of NN% width, positioned at the inner-area start of the full bar."""
    if pct <= 0:
        return
    yob, yot, yib, yit = _y_bounds(p)
    fx0, fx1 = _full_inner_x(p)
    inner_w = fx1 - fx0
    drawn = max(1, round(inner_w * pct / 100))
    _rect(pen, fx0, yib, fx0 + drawn, yit)


def _draw_full_base(pen, p, pct):
    """Monochrome fallback: full track + colored fill, both in foreground color."""
    _draw_full_track(pen, p)
    _draw_full_fill(pen, p, pct)


# ---------------------------------------------------------------------------
# Glyph registration
# ---------------------------------------------------------------------------

def draw_progress_h_glyphs(glyph_data, params=None):
    """Add horizontal progress bar glyphs to glyph_data."""
    if params is None:
        params = FontParams()
    p = params

    # --- Markers (zero-width, never rendered) ---
    glyph_data["prog_h_sep"] = (0, None)
    for d in range(10):
        glyph_data[f"prog_h_d{d}"] = (0, None)

    # --- Drawing sub-glyphs (COLR layers) ---
    glyph_data["prog_h_open_track"] = (
        p.h_open_advance, lambda pen: _draw_open_track(pen, p)
    )
    glyph_data["prog_h_close_track"] = (
        p.h_close_advance, lambda pen: _draw_close_track(pen, p)
    )

    for pct in range(0, 101):
        adv = _seg_advance(p, pct)
        def make_strip(pct_=pct):
            return lambda pen: _draw_strip(pen, p, pct_)
        def make_fill(pct_=pct):
            return lambda pen: _draw_fill(pen, p, pct_)
        glyph_data[f"prog_h_strip_{pct}"] = (adv, make_strip())
        glyph_data[f"prog_h_fill_{pct}"]  = (adv, make_fill())

    # --- Composite COLR base glyphs ---
    # Opener
    glyph_data["prog_h_open"] = (
        p.h_open_advance, lambda pen: _draw_open_base(pen, p)
    )
    # Closer
    glyph_data["prog_h_close"] = (
        p.h_close_advance, lambda pen: _draw_close_base(pen, p)
    )

    # Segments at each position (1..MAX_SEGMENTS)
    for pos in range(1, MAX_SEGMENTS + 1):
        for pct in range(0, 101):
            adv = _seg_advance(p, pct)
            def make_seg(pct_=pct):
                return lambda pen: _draw_seg_base(pen, p, pct_)
            glyph_data[f"prog_h_seg_{pct}_pos{pos}"] = (adv, make_seg())

    # --- Fixed-width single-segment baked glyphs (for {h:NN} direct ligature) ---
    glyph_data["prog_h_full_track"] = (
        p.h_bar_width, lambda pen: _draw_full_track(pen, p)
    )
    for pct in range(0, 101):
        def make_full_fill(pct_=pct):
            return lambda pen: _draw_full_fill(pen, p, pct_)
        glyph_data[f"prog_h_full_fill_{pct}"] = (p.h_bar_width, make_full_fill())

        def make_full_base(pct_=pct):
            return lambda pen: _draw_full_base(pen, p, pct_)
        glyph_data[f"prog_h_full_{pct}"] = (p.h_bar_width, make_full_base())


def colr_layers_h():
    """Return COLR layer mapping for all horizontal composite glyphs."""
    layers = {
        "prog_h_open":  [("prog_h_open_track", 0)],
        "prog_h_close": [("prog_h_close_track", 0)],
    }
    for pos in range(1, MAX_SEGMENTS + 1):
        for pct in range(0, 101):
            layers[f"prog_h_seg_{pct}_pos{pos}"] = [
                (f"prog_h_strip_{pct}", 0),
                (f"prog_h_fill_{pct}",  pos),  # palette index = position
            ]
    # Fixed-width single-segment bars — track at palette[0], fill at palette[1].
    for pct in range(0, 101):
        layers[f"prog_h_full_{pct}"] = [
            ("prog_h_full_track", 0),
            (f"prog_h_full_fill_{pct}", 1),
        ]
    return layers


# ---------------------------------------------------------------------------
# OpenType feature code
# ---------------------------------------------------------------------------

def generate_progress_h_full_liga_code():
    """Generate direct ligature code for {h:NN} -> prog_h_full_NN.

    These ligatures take priority over the multi-segment open ligature (since
    they match a longer sequence including the closing brace). Produces a
    fixed-width single-segment bar where the colored fill grows from the left
    and the remainder shows as empty track.
    """
    lines = []
    lines.append("lookup prog_h_full_liga {")
    # 3-digit: {h:100}
    seq_100 = "uni007B uni0068 uni003A uni0031 uni0030 uni0030 uni007D"
    lines.append(f"  sub {seq_100} by prog_h_full_100;")
    # 2-digit: {h:10}..{h:99}
    for tens in range(1, 10):
        for ones in range(0, 10):
            pct = tens * 10 + ones
            seq = (
                f"uni007B uni0068 uni003A "
                f"uni003{tens} uni003{ones} uni007D"
            )
            lines.append(f"  sub {seq} by prog_h_full_{pct};")
    # 1-digit: {h:0}..{h:9}
    for d in range(0, 10):
        seq = f"uni007B uni0068 uni003A uni003{d} uni007D"
        lines.append(f"  sub {seq} by prog_h_full_{d};")
    lines.append("} prog_h_full_liga;")
    return "\n".join(lines)


def generate_progress_h_feature_code():
    """Generate calt feature code for horizontal multi-segment progress bars."""
    lines = []

    # --- Glyph classes ---
    digits_uni = [f"uni003{d}" for d in range(10)]
    digit_intermediates = [f"prog_h_d{d}" for d in range(10)]
    lines.append(f"@h_digits = [{' '.join(digits_uni)}];")
    lines.append(f"@h_d = [{' '.join(digit_intermediates)}];")

    propagate_ctx = ["prog_h_open", "prog_h_sep"] + digit_intermediates
    lines.append(f"@h_prop_ctx = [{' '.join(propagate_ctx)}];")

    # Per-position segment classes
    for pos in range(1, MAX_SEGMENTS + 1):
        names = [f"prog_h_seg_{pct}_pos{pos}" for pct in range(0, 101)]
        lines.append(f"@h_segs_pos{pos} = [{' '.join(names)}];")

    # All positioned segments (for close context)
    all_seg_classes = [f"@h_segs_pos{pos}" for pos in range(1, MAX_SEGMENTS + 1)]
    close_ctx = ["prog_h_open", "prog_h_sep"] + [
        f"prog_h_seg_{pct}_pos{pos}"
        for pos in range(1, MAX_SEGMENTS + 1)
        for pct in range(0, 101)
    ]
    lines.append(f"@h_close_ctx = [{' '.join(close_ctx)}];")
    lines.append("")

    # --- Lookup: open ligature {h: → prog_h_open ---
    lines.append("lookup prog_h_open_liga {")
    lines.append("  sub uni007B uni0068 uni003A by prog_h_open;")
    lines.append("} prog_h_open_liga;")
    lines.append("")

    # --- Lookup: digit/comma → intermediate ---
    lines.append("lookup prog_h_to_digit {")
    for d in range(10):
        lines.append(f"  sub uni003{d} by prog_h_d{d};")
    lines.append("} prog_h_to_digit;")
    lines.append("")

    lines.append("lookup prog_h_to_sep {")
    lines.append("  sub uni002C by prog_h_sep;")
    lines.append("} prog_h_to_sep;")
    lines.append("")

    # --- Lookup: propagate (chained calt) ---
    lines.append("lookup prog_h_propagate {")
    lines.append("  sub @h_prop_ctx @h_digits' lookup prog_h_to_digit;")
    lines.append("  sub @h_prop_ctx uni002C' lookup prog_h_to_sep;")
    lines.append("} prog_h_propagate;")
    lines.append("")

    # --- Per-position combine lookups (ligature) ---
    # Each position has its own combine lookup that produces seg_NN_posK glyphs.
    for pos in range(1, MAX_SEGMENTS + 1):
        lines.append(f"lookup prog_h_combine_pos{pos} {{")
        # 3-digit: 100
        lines.append(
            f"  sub prog_h_d1 prog_h_d0 prog_h_d0 by prog_h_seg_100_pos{pos};"
        )
        # 2-digit: 10..99
        for tens in range(1, 10):
            for ones in range(0, 10):
                val = tens * 10 + ones
                lines.append(
                    f"  sub prog_h_d{tens} prog_h_d{ones} "
                    f"by prog_h_seg_{val}_pos{pos};"
                )
        # 1-digit: 0..9
        for d in range(0, 10):
            lines.append(f"  sub prog_h_d{d} by prog_h_seg_{d}_pos{pos};")
        lines.append(f"}} prog_h_combine_pos{pos};")
        lines.append("")

    # --- Per-position chain rules ---
    # Position 1: digits directly after prog_h_open
    for pos in range(1, MAX_SEGMENTS + 1):
        lines.append(f"lookup prog_h_chain_pos{pos} {{")
        if pos == 1:
            prefix = "prog_h_open"
        else:
            prefix = f"@h_segs_pos{pos-1} prog_h_sep"
        # FEA "lookup" directive binds to the immediately-preceding marked glyph.
        # Place it after the FIRST mark so the ligature can consume forward
        # through subsequent marked digits.
        # 3-digit: open d' lookup d' d'
        lines.append(
            f"  sub {prefix} @h_d' lookup prog_h_combine_pos{pos} @h_d' @h_d';"
        )
        # 2-digit
        lines.append(
            f"  sub {prefix} @h_d' lookup prog_h_combine_pos{pos} @h_d';"
        )
        # 1-digit
        lines.append(
            f"  sub {prefix} @h_d' lookup prog_h_combine_pos{pos};"
        )
        lines.append(f"}} prog_h_chain_pos{pos};")
        lines.append("")

    # --- Lookup: close ---
    lines.append("lookup prog_h_close_sub {")
    lines.append("  sub uni007D by prog_h_close;")
    lines.append("} prog_h_close_sub;")
    lines.append("")

    lines.append("lookup prog_h_close_chain {")
    lines.append("  sub @h_close_ctx uni007D' lookup prog_h_close_sub;")
    lines.append("} prog_h_close_chain;")
    lines.append("")

    return "\n".join(lines)


def progress_h_calt_lookups():
    """Return ordered list of lookup names for the calt feature."""
    names = [
        "prog_h_open_liga",
        "prog_h_propagate",
    ]
    for pos in range(1, MAX_SEGMENTS + 1):
        names.append(f"prog_h_chain_pos{pos}")
    names.append("prog_h_close_chain")
    return names
