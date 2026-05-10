"""Font assembly: monochrome TrueType outlines + variable axes.

Builds:
- Static masters (build_font) — TTF (monochrome, foreground-coloured via CSS)
- Variable font (build_variable_font) — merges masters via varLib
- Static instances (export_static_instance) — pinned slices of the VF

NOTE: COLR/CPAL was removed because Chrome's Skia + DirectWrite GPU
rasterisation path on Windows is unreliable for COLR fonts (intermittent
"Aw, snap" renderer crashes during scroll/idle repaints, stable in software
rendering and in Firefox). Bars are rendered monochrome and tinted via CSS
`color`, matching the architecture of the Datatype font.
"""

import copy
import os
from datetime import datetime, timedelta

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.designspaceLib import (
    DesignSpaceDocument, SourceDescriptor, AxisDescriptor, InstanceDescriptor,
)
from fontTools import varLib
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.otlLib.builder import buildStatTable

from sources.config import (
    UPM, FAMILY_NAME, REGULAR_STYLE, FONT_VERSION,
    CAP_HEIGHT, X_HEIGHT,
    TYPO_ASCENDER, TYPO_DESCENDER, WIN_ASCENT, WIN_DESCENT,
)


def _font_revision_float():
    _major, _minor, *_ = (FONT_VERSION + ".0.0").split(".")
    return float(f"{_major}.{_minor}")


def build_font(glyph_data, feature_code,
               style=REGULAR_STYLE, family_name=FAMILY_NAME):
    """Build one static master TTF (monochrome — no COLR/CPAL).

    Args:
        glyph_data: dict {glyph_name: (advance_width, draw_func_or_None)}
        feature_code: OpenType feature code string
    """
    if ".notdef" not in glyph_data:
        raise ValueError(".notdef glyph is required")

    glyph_names = [".notdef"] + [n for n in glyph_data if n != ".notdef"]

    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(glyph_names)

    cmap = {}
    for name in glyph_names:
        if name.startswith("uni") and len(name) == 7:
            try:
                cmap[int(name[3:], 16)] = name
            except ValueError:
                pass
    if "space" in glyph_names:
        cmap[0x0020] = "space"
    fb.setupCharacterMap(cmap)

    glyph_table = {}
    for name in glyph_names:
        pen = TTGlyphPen(None)
        width, draw_func = glyph_data[name]
        if draw_func is not None:
            draw_func(pen)
        glyph_table[name] = pen.glyph()
    fb.setupGlyf(glyph_table)

    metrics = {}
    for name in glyph_names:
        width = glyph_data[name][0]
        glyph = glyph_table[name]
        if hasattr(glyph, "xMin") and glyph.xMin is not None:
            lsb = glyph.xMin
        else:
            lsb = 0
        metrics[name] = (width, lsb)
    fb.setupHorizontalMetrics(metrics)

    fb.setupHorizontalHeader(ascent=TYPO_ASCENDER, descent=TYPO_DESCENDER)
    fb.setupNameTable({
        "familyName": family_name,
        "styleName": style,
        "copyright": "Copyright 2026 The ProgressType Project Authors",
        "manufacturer": "ProgressType Project",
        "licenseDescription": "This Font Software is licensed under the SIL Open Font License, Version 1.1.",
        "licenseInfoURL": "https://openfontlicense.org",
    })
    fb.setupOS2(
        sTypoAscender=TYPO_ASCENDER,
        sTypoDescender=TYPO_DESCENDER,
        sTypoLineGap=0,
        usWinAscent=WIN_ASCENT,
        usWinDescent=WIN_DESCENT,
        sxHeight=X_HEIGHT,
        sCapHeight=CAP_HEIGHT,
        achVendID="PRTY",
        fsType=0x0000,
        fsSelection=0x00C0,
        usWidthClass=5,
        version=4,
    )
    fb.setupPost()

    now = datetime.now()
    epoch_1904 = datetime(1904, 1, 1)
    created_seconds = int((now - timedelta(days=1) - epoch_1904).total_seconds())
    modified_seconds = int((now - epoch_1904).total_seconds())
    fb.setupHead(
        unitsPerEm=UPM,
        flags=0b00010000,
        created=created_seconds,
        modified=modified_seconds,
    )
    fb.font["head"].fontRevision = _font_revision_float()

    if feature_code:
        fb.addOpenTypeFeatures(feature_code)

    font = fb.font

    # gasp, post
    from fontTools.ttLib.tables._g_a_s_p import table__g_a_s_p
    gasp = table__g_a_s_p()
    gasp.gaspRange = {0xFFFF: 0x000F}
    font["gasp"] = gasp
    font["post"].isFixedPitch = 0

    # COLR/CPAL intentionally NOT added — Chrome's Skia + DirectWrite GPU
    # rasteriser crashes intermittently on COLR fonts (skia issue 338390594
    # and Mozilla bug 1933050 document the broader Skia+DirectWrite COLR
    # fragility). Bars render via the monochrome base glyph outlines
    # (_draw_*_base) which include track frame + fill drawn together in
    # foreground colour.

    # name table — strip Mac platform records
    name_table = font["name"]
    name_table.names = [r for r in name_table.names if r.platformID != 1]

    return font


def build_variable_font(master_fonts, axes_config, named_instances=None):
    """Merge static masters into a single variable font.

    Args:
        master_fonts: list of (TTFont, location_dict) — location uses axis Names
            e.g. {"Width": 100, "Weight": 400}
        axes_config: list of (tag, name, min, default, max) tuples
        named_instances: list of (style_name, location_dict)

    Returns:
        TTFont — variable font with fvar/gvar/STAT tables
    """
    ds = DesignSpaceDocument()

    for tag, name, min_val, default_val, max_val in axes_config:
        axis = AxisDescriptor()
        axis.tag = tag
        axis.name = name
        axis.minimum = min_val
        axis.default = default_val
        axis.maximum = max_val
        ds.addAxis(axis)

    for i, (font, location) in enumerate(master_fonts):
        src = SourceDescriptor()
        src.font = font
        src.location = location
        if i == 0:
            src.copyLib = True
            src.copyFeatures = True
            src.copyGroups = True
            src.copyInfo = True
        ds.addSource(src)

    if named_instances:
        for style_name, location in named_instances:
            inst = InstanceDescriptor()
            inst.styleName = style_name
            inst.location = location
            ds.addInstance(inst)

    vf, _, _ = varLib.build(ds)
    vf["head"].fontRevision = _font_revision_float()

    # STAT table — required for variable fonts with named instances
    stat_axes = [
        dict(tag="wdth", name="Width", values=[
            dict(value=50,    name="UltraCondensed"),
            dict(value=62.5,  name="ExtraCondensed"),
            dict(value=75,    name="Condensed"),
            dict(value=87.5,  name="SemiCondensed"),
            dict(value=100,   name="Normal", flags=0x2),  # ElidableAxisValueName
            dict(value=112.5, name="SemiExpanded"),
            dict(value=125,   name="Expanded"),
            dict(value=150,   name="ExtraExpanded"),
        ]),
        dict(tag="wght", name="Weight", values=[
            dict(value=100, name="Thin"),
            dict(value=200, name="ExtraLight"),
            dict(value=300, name="Light"),
            dict(value=400, name="Regular", flags=0x2, linkedValue=700.0),
            dict(value=500, name="Medium"),
            dict(value=600, name="SemiBold"),
            dict(value=700, name="Bold"),
            dict(value=800, name="ExtraBold"),
            dict(value=900, name="Black"),
        ]),
    ]
    buildStatTable(vf, stat_axes)

    # Strip Mac platform name records
    vf["name"].names = [r for r in vf["name"].names if r.platformID != 1]

    vf["OS/2"].usWidthClass = 5

    # Variations PostScript Name Prefix
    vf["name"].setName(FAMILY_NAME, 25, 3, 1, 0x0409)

    return vf


def clean_static_glyphs(static):
    """Strip degenerate outline operations inherited from the variable font's
    coincident-point compatibility tricks (arc points collapsing onto corners
    at RADI=0). Also drop residual variable-font tables (STAT) that
    instantiateVariableFont leaves behind even when all axes are pinned.

    Filters out:
      - lineTo segments of zero length (start == end)
      - qCurveTo where every off-curve and the on-curve endpoint all coincide
        with the pen's current point (a no-op curve at RADI=0)

    NOTE: skia-pathops `removeOverlaps` is intentionally NOT run here. It
    corrupts our pill-shaped tracks: the zero-length top/bottom edges plus
    quadratic-Bézier arcs confuse its Op pipeline, producing flattened
    rectangles instead of properly rounded ends.
    """
    # Drop STAT — vestigial style-attribute metadata pointing at axes that no
    # longer exist on this static instance. Chrome/Skia path-throws on a few
    # COLR + variable-table-leftover combinations.
    if "STAT" in static:
        del static["STAT"]
    from fontTools.pens.recordingPen import RecordingPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    glyph_set = static.getGlyphSet()
    glyf = static["glyf"]
    for name in static.getGlyphOrder():
        glyph = glyf[name]
        if glyph.numberOfContours <= 0:
            continue
        rec = RecordingPen()
        glyph_set[name].draw(rec)

        pen = TTGlyphPen(None)
        last_pt = None
        changed = False
        for op, args in rec.value:
            if op == "moveTo":
                pen.moveTo(args[0])
                last_pt = args[0]
            elif op == "lineTo":
                if args[0] == last_pt:
                    changed = True
                    continue
                pen.lineTo(args[0])
                last_pt = args[0]
            elif op == "qCurveTo":
                if last_pt is not None and all(pt == last_pt for pt in args):
                    changed = True
                    continue
                pen.qCurveTo(*args)
                last_pt = args[-1] if args else last_pt
            elif op == "curveTo":
                pen.curveTo(*args)
                last_pt = args[-1] if args else last_pt
            elif op == "closePath":
                pen.closePath()
                last_pt = None
            elif op == "endPath":
                pen.endPath()
                last_pt = None
        if changed:
            glyf[name] = pen.glyph()


def export_static_instance(vf, location, output_dir, basename, style_name,
                           weight_class, woff2_dir=None):
    """Export a static instance pinned at `location` from the variable font."""
    static = instantiateVariableFont(copy.deepcopy(vf), location)
    clean_static_glyphs(static)

    _WGHT_NAMES = {
        100: "Thin", 200: "ExtraLight", 300: "Light", 400: "Regular",
        500: "Medium", 600: "SemiBold", 700: "Bold", 800: "ExtraBold", 900: "Black",
    }
    wght = int(location.get("wght", weight_class))
    weight_name = _WGHT_NAMES.get(wght, str(wght))

    is_classic = wght in (400, 700)
    if is_classic:
        family_name_id1 = basename
        subfamily_id2 = weight_name
        full_name = f"{basename} {weight_name}"
        ps_name = f"{basename}-{weight_name}"
        typo_family = None
        typo_subfamily = None
        fs_selection = 0x00A0 if wght == 700 else 0x00C0
        mac_style = 0x0001 if wght == 700 else 0
    else:
        family_name_id1 = f"{basename} {weight_name}"
        subfamily_id2 = "Regular"
        full_name = family_name_id1
        ps_name = f"{basename}-{weight_name}"
        typo_family = basename
        typo_subfamily = weight_name
        fs_selection = 0x00C0
        mac_style = 0

    name_table = static["name"]
    name_table.names = [r for r in name_table.names if r.platformID != 1]
    name_table.setName(family_name_id1, 1, 3, 1, 0x0409)
    name_table.setName(subfamily_id2, 2, 3, 1, 0x0409)
    name_table.setName(full_name, 4, 3, 1, 0x0409)
    name_table.setName(ps_name, 6, 3, 1, 0x0409)
    if typo_family is not None:
        name_table.setName(typo_family, 16, 3, 1, 0x0409)
        name_table.setName(typo_subfamily, 17, 3, 1, 0x0409)
    else:
        name_table.names = [r for r in name_table.names if r.nameID not in (16, 17)]

    static["OS/2"].usWeightClass = weight_class
    static["OS/2"].fsSelection = fs_selection
    static["head"].macStyle = mac_style

    os.makedirs(output_dir, exist_ok=True)
    ttf_path = os.path.join(output_dir, f"{ps_name}.ttf")
    static.save(ttf_path)
    print(f"    {ttf_path}")

    woff2_output_dir = woff2_dir if woff2_dir else output_dir
    os.makedirs(woff2_output_dir, exist_ok=True)
    static.flavor = "woff2"
    woff2_path = os.path.join(woff2_output_dir, f"{ps_name}.woff2")
    static.save(woff2_path)
    print(f"    {woff2_path}")
