"""Vertical progress bar glyphs and ligature feature code.

Same structure as progress_h, parameterized via FontParams.
Fill grows upward from the bottom of the inner area.
"""

import math

from sources.config import FontParams


_ARC_N = 8  # polyline segments per quarter-arc; must match across masters


def _rect(pen, x0, y0, x1, y1):
    pen.moveTo((x0, y0))
    pen.lineTo((x1, y0))
    pen.lineTo((x1, y1))
    pen.lineTo((x0, y1))
    pen.closePath()


def _arc_intermediate(cx, cy, r, start_deg, end_deg, n=_ARC_N):
    for i in range(1, n):
        t = i / n
        theta = math.radians(start_deg + t * (end_deg - start_deg))
        yield (cx + r * math.cos(theta), cy + r * math.sin(theta))


def _track_metrics(p):
    x0 = p.v_bar_lead
    y0 = p.v_bar_baseline
    x1 = p.v_bar_lead + (p.v_bar_width - p.v_bar_lead - p.v_bar_trail)
    y1 = p.v_bar_baseline + p.v_bar_height

    fx0 = x0 + p.v_bar_border + p.v_bar_padding + p.v_bar_radius
    fy0 = y0 + p.v_bar_border + p.v_bar_padding + p.v_bar_radius
    fx1 = x1 - p.v_bar_border - p.v_bar_padding - p.v_bar_radius
    fy1 = y1 - p.v_bar_border - p.v_bar_padding - p.v_bar_radius

    return (x0, y0, x1, y1), (fx0, fy0, fx1, fy1)


def _draw_track(pen, p):
    """Outer rounded rectangle CCW + inner rounded rectangle CW (hole).

    At v_bar_radius=0 collapses to the original two nested rectangles.
    """
    (x0, y0, x1, y1), _ = _track_metrics(p)
    R = p.v_bar_radius
    border = p.v_bar_border
    ir = max(R - border, 0)  # inner radius; clamped (interpolation acceptable for our masters)

    # Outer outline, CCW: bottom edge → bot-right arc → right → top-right arc → top → top-left arc → left → bot-left arc.
    pen.moveTo((x0 + R, y0))
    pen.lineTo((x1 - R, y0))
    for pt in _arc_intermediate(x1 - R, y0 + R, R, 270, 360):
        pen.lineTo(pt)
    pen.lineTo((x1, y0 + R))
    pen.lineTo((x1, y1 - R))
    for pt in _arc_intermediate(x1 - R, y1 - R, R, 0, 90):
        pen.lineTo(pt)
    pen.lineTo((x1 - R, y1))
    pen.lineTo((x0 + R, y1))
    for pt in _arc_intermediate(x0 + R, y1 - R, R, 90, 180):
        pen.lineTo(pt)
    pen.lineTo((x0, y1 - R))
    pen.lineTo((x0, y0 + R))
    for pt in _arc_intermediate(x0 + R, y0 + R, R, 180, 270):
        pen.lineTo(pt)
    pen.closePath()

    # Inner outline (hole), CW: opposite winding around concentric inner radius.
    ix0, iy0 = x0 + border, y0 + border
    ix1, iy1 = x1 - border, y1 - border
    pen.moveTo((ix0 + ir, iy0))
    for pt in _arc_intermediate(ix0 + ir, iy0 + ir, ir, 270, 180):
        pen.lineTo(pt)
    pen.lineTo((ix0, iy0 + ir))
    pen.lineTo((ix0, iy1 - ir))
    for pt in _arc_intermediate(ix0 + ir, iy1 - ir, ir, 180, 90):
        pen.lineTo(pt)
    pen.lineTo((ix0 + ir, iy1))
    pen.lineTo((ix1 - ir, iy1))
    for pt in _arc_intermediate(ix1 - ir, iy1 - ir, ir, 90, 0):
        pen.lineTo(pt)
    pen.lineTo((ix1, iy1 - ir))
    pen.lineTo((ix1, iy0 + ir))
    for pt in _arc_intermediate(ix1 - ir, iy0 + ir, ir, 0, -90):
        pen.lineTo(pt)
    pen.lineTo((ix1 - ir, iy0))
    pen.closePath()


def _draw_fill(pen, p, pct):
    if pct <= 0:
        return
    _, (fx0, fy0, fx1, fy1) = _track_metrics(p)
    height = fy1 - fy0
    drawn = max(1, round(height * pct / 100))
    _rect(pen, fx0, fy0, fx1, fy0 + drawn)


def _draw_base(pen, p, pct):
    _draw_track(pen, p)
    _draw_fill(pen, p, pct)


def draw_progress_v_glyphs(glyph_data, params=None):
    if params is None:
        params = FontParams()
    p = params

    glyph_data["prog_v_track"] = (p.v_bar_width, lambda pen: _draw_track(pen, p))

    for pct in range(0, 101):
        def make_fill(pct_=pct):
            return lambda pen: _draw_fill(pen, p, pct_)
        glyph_data[f"prog_v_fill_{pct}"] = (p.v_bar_width, make_fill())

        def make_base(pct_=pct):
            return lambda pen: _draw_base(pen, p, pct_)
        glyph_data[f"prog_v_{pct}"] = (p.v_bar_width, make_base())


def colr_layers_v():
    return {
        f"prog_v_{pct}": [
            ("prog_v_track", 0),
            (f"prog_v_fill_{pct}", 1),
        ]
        for pct in range(0, 101)
    }


def generate_progress_v_feature_code():
    """Generate ligature feature code for {v:NN} → prog_v_NN."""
    lines = []
    lines.append("lookup prog_v_liga {")
    seq_100 = "uni007B uni0076 uni003A uni0031 uni0030 uni0030 uni007D"
    lines.append(f"  sub {seq_100} by prog_v_100;")
    for tens in range(1, 10):
        for ones in range(0, 10):
            pct = tens * 10 + ones
            seq = (
                f"uni007B uni0076 uni003A "
                f"uni003{tens} uni003{ones} uni007D"
            )
            lines.append(f"  sub {seq} by prog_v_{pct};")
    for d in range(0, 10):
        seq = f"uni007B uni0076 uni003A uni003{d} uni007D"
        lines.append(f"  sub {seq} by prog_v_{d};")
    lines.append("} prog_v_liga;")
    return "\n".join(lines)
