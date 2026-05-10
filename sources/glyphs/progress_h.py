"""Horizontal progress bar glyphs and ligature feature code.

Architecture: each `{h:NN}` ligature (NN ∈ 0..100) substitutes to a single
prog_h_full_NN glyph that bakes the entire bar — outer rounded track frame
plus the percentage-width fill — into one monochrome outline. Tinted via
CSS `color`.

Multi-segment bars (`{h:NN,MM,...}`) were removed because their rendering
relied on COLR/CPAL color layers, and Chrome's Skia + DirectWrite GPU
rasteriser crashes intermittently on COLR fonts on Windows. Once browser
font engines settle on a stable color-font path we can re-introduce them.
"""

import math

from sources.config import FontParams


# Each arc is rendered as N_QUADS quadratic Béziers using qCurveTo with the
# TrueType "implied on-curve" trick. Two segments per quarter arc give ~0.3%
# deviation from a true circle and rasterise efficiently on the GPU.
_ARC_N_QUADS = 2


def _rect(pen, x0, y0, x1, y1):
    pen.moveTo((x0, y0))
    pen.lineTo((x1, y0))
    pen.lineTo((x1, y1))
    pen.lineTo((x0, y1))
    pen.closePath()


def _arc_qcurve_args(cx, cy, r, start_deg, end_deg, n_quads=_ARC_N_QUADS):
    """Build the args for `pen.qCurveTo(*args)` to draw an arc as quadratic Béziers.

    Returns a list of (n_quads + 1) points: n_quads off-curve control points
    followed by the on-curve endpoint at end_deg. The pen's current point must
    already be at start_deg before calling.

    At r=0 every returned point collapses to (cx, cy) — flag/structure stays
    constant so varLib can interpolate between square (r=0) and rounded
    (r>0) masters.
    """
    if r == 0:
        return [(cx, cy)] * (n_quads + 1)

    sub_span_deg = (end_deg - start_deg) / n_quads
    d = r * math.tan(abs(math.radians(sub_span_deg)) / 2)
    sign = 1 if sub_span_deg > 0 else -1

    # Round to int — float epsilon at cardinal angles (cos(270°) ≈ 6e-17 instead
    # of exactly 0) leaks into endpoint coordinates and breaks TTGlyphPen's
    # closePath dedup, which then breaks varLib's master compatibility.
    pts = []
    for i in range(n_quads):
        a = math.radians(start_deg + i * sub_span_deg)
        ax = cx + r * math.cos(a)
        ay = cy + r * math.sin(a)
        pts.append((round(ax + sign * d * (-math.sin(a))),
                    round(ay + sign * d * math.cos(a))))

    e = math.radians(end_deg)
    pts.append((round(cx + r * math.cos(e)), round(cy + r * math.sin(e))))
    return pts


def _y_bounds(p):
    """Inner-area y-bounds for the fill (between top and bottom borders)."""
    y_outer_bottom = p.h_bar_baseline
    y_outer_top = p.h_bar_baseline + p.h_bar_height
    y_inner_bottom = y_outer_bottom + p.h_bar_border + p.h_bar_padding
    y_inner_top = y_outer_top - p.h_bar_border - p.h_bar_padding
    return y_outer_bottom, y_outer_top, y_inner_bottom, y_inner_top


def _full_inner_x(p):
    """Return (x_inner_start, x_inner_end) within the full bar coordinate space.

    Inset by h_bar_radius on both ends so the fill stays inside the rectangular
    middle band; the rounded end-cap regions remain track-coloured.
    """
    x0 = p.h_bar_lead + p.h_bar_border + p.h_bar_padding + p.h_bar_radius
    x1 = p.h_bar_width - p.h_bar_trail - p.h_bar_border - p.h_bar_padding - p.h_bar_radius
    return x0, x1


def _draw_full_track(pen, p):
    """Full-width track frame: outer rounded-rect + inner rounded-rect hole."""
    yob, yot, yib, yit = _y_bounds(p)
    R = p.h_bar_radius
    border = p.h_bar_border
    ir = max(R - border, 0)

    x0 = p.h_bar_lead
    x1 = p.h_bar_width - p.h_bar_trail

    # Outer outline, CCW.
    outer_start = (x0 + R, yob)
    pen.moveTo(outer_start)
    pen.lineTo((x1 - R, yob))
    pen.qCurveTo(*_arc_qcurve_args(x1 - R, yob + R, R, 270, 360))
    pen.lineTo((x1, yot - R))
    pen.qCurveTo(*_arc_qcurve_args(x1 - R, yot - R, R, 0, 90))
    pen.lineTo((x0 + R, yot))
    pen.qCurveTo(*_arc_qcurve_args(x0 + R, yot - R, R, 90, 180))
    pen.lineTo((x0, yob + R))
    pen.qCurveTo(*_arc_qcurve_args(x0 + R, yob + R, R, 180, 270))
    pen.lineTo(outer_start)
    pen.closePath()

    # Inner hole, CW (concentric, inset by border on every side).
    ix0, ix1 = x0 + border, x1 - border
    inner_start = (ix0 + ir, yib)
    pen.moveTo(inner_start)
    pen.qCurveTo(*_arc_qcurve_args(ix0 + ir, yib + ir, ir, 270, 180))
    pen.lineTo((ix0, yit - ir))
    pen.qCurveTo(*_arc_qcurve_args(ix0 + ir, yit - ir, ir, 180, 90))
    pen.lineTo((ix1 - ir, yit))
    pen.qCurveTo(*_arc_qcurve_args(ix1 - ir, yit - ir, ir, 90, 0))
    pen.lineTo((ix1, yib + ir))
    pen.qCurveTo(*_arc_qcurve_args(ix1 - ir, yib + ir, ir, 0, -90))
    pen.lineTo(inner_start)
    pen.closePath()


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
    """Track frame + fill, both in foreground colour."""
    _draw_full_track(pen, p)
    _draw_full_fill(pen, p, pct)


def draw_progress_h_glyphs(glyph_data, params=None):
    """Add horizontal progress bar glyphs (prog_h_full_0..prog_h_full_100)."""
    if params is None:
        params = FontParams()
    p = params

    for pct in range(0, 101):
        def make_full_base(pct_=pct):
            return lambda pen: _draw_full_base(pen, p, pct_)
        glyph_data[f"prog_h_full_{pct}"] = (p.h_bar_width, make_full_base())


def generate_progress_h_full_liga_code():
    """Generate ligature code for {h:NN} → prog_h_full_NN."""
    lines = []
    lines.append("lookup prog_h_full_liga {")
    seq_100 = "uni007B uni0068 uni003A uni0031 uni0030 uni0030 uni007D"
    lines.append(f"  sub {seq_100} by prog_h_full_100;")
    for tens in range(1, 10):
        for ones in range(0, 10):
            pct = tens * 10 + ones
            seq = (
                f"uni007B uni0068 uni003A "
                f"uni003{tens} uni003{ones} uni007D"
            )
            lines.append(f"  sub {seq} by prog_h_full_{pct};")
    for d in range(0, 10):
        seq = f"uni007B uni0068 uni003A uni003{d} uni007D"
        lines.append(f"  sub {seq} by prog_h_full_{d};")
    lines.append("} prog_h_full_liga;")
    return "\n".join(lines)
