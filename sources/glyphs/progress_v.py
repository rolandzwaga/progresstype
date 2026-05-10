"""Vertical progress bar glyphs and ligature feature code.

Same structure as progress_h, parameterized via FontParams.
Fill grows upward from the bottom of the inner area.
"""

from sources.config import FontParams
from sources.glyphs.progress_h import _arc_qcurve_args


def _rect(pen, x0, y0, x1, y1):
    pen.moveTo((x0, y0))
    pen.lineTo((x1, y0))
    pen.lineTo((x1, y1))
    pen.lineTo((x0, y1))
    pen.closePath()


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

    # Outer outline, CCW. Each contour ends with an explicit lineTo back to
    # moveTo so TTGlyphPen.closePath always pops one redundant point — this
    # keeps point structure identical across masters even when pill radii
    # cause the last arc end to naturally coincide with moveTo.
    outer_start = (x0 + R, y0)
    pen.moveTo(outer_start)
    pen.lineTo((x1 - R, y0))
    pen.qCurveTo(*_arc_qcurve_args(x1 - R, y0 + R, R, 270, 360))
    pen.lineTo((x1, y1 - R))
    pen.qCurveTo(*_arc_qcurve_args(x1 - R, y1 - R, R, 0, 90))
    pen.lineTo((x0 + R, y1))
    pen.qCurveTo(*_arc_qcurve_args(x0 + R, y1 - R, R, 90, 180))
    pen.lineTo((x0, y0 + R))
    pen.qCurveTo(*_arc_qcurve_args(x0 + R, y0 + R, R, 180, 270))
    pen.lineTo(outer_start)
    pen.closePath()

    # Inner outline (hole), CW: opposite winding around concentric inner radius.
    ix0, iy0 = x0 + border, y0 + border
    ix1, iy1 = x1 - border, y1 - border
    inner_start = (ix0 + ir, iy0)
    pen.moveTo(inner_start)
    pen.qCurveTo(*_arc_qcurve_args(ix0 + ir, iy0 + ir, ir, 270, 180))
    pen.lineTo((ix0, iy1 - ir))
    pen.qCurveTo(*_arc_qcurve_args(ix0 + ir, iy1 - ir, ir, 180, 90))
    pen.lineTo((ix1 - ir, iy1))
    pen.qCurveTo(*_arc_qcurve_args(ix1 - ir, iy1 - ir, ir, 90, 0))
    pen.lineTo((ix1, iy0 + ir))
    pen.qCurveTo(*_arc_qcurve_args(ix1 - ir, iy0 + ir, ir, 0, -90))
    pen.lineTo(inner_start)
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
    """Add vertical progress bar glyphs (prog_v_0..prog_v_100)."""
    if params is None:
        params = FontParams()
    p = params

    for pct in range(0, 101):
        def make_base(pct_=pct):
            return lambda pen: _draw_base(pen, p, pct_)
        glyph_data[f"prog_v_{pct}"] = (p.v_bar_width, make_base())


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
