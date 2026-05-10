"""ProgressType build: variable font + static instances."""

import os
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from sources.config import (
    FAMILY_NAME, AXIS_MASTERS, NAMED_INSTANCES, params_for_master,
)
from sources.glyphs.base_imported import draw_base_glyphs
from sources.glyphs.progress_h import (
    draw_progress_h_glyphs, generate_progress_h_full_liga_code,
    generate_progress_h_ss01_code,
)
from sources.glyphs.progress_v import (
    draw_progress_v_glyphs, generate_progress_v_feature_code,
)
from sources.font_builder import (
    build_font, build_variable_font, export_static_instance, clean_static_glyphs,
)
from sources.export import export_font


def _feature_code():
    h_full_fea = generate_progress_h_full_liga_code()
    h_ss01_fea = generate_progress_h_ss01_code()
    v_fea = generate_progress_v_feature_code()

    return f"""
{h_full_fea}

{h_ss01_fea}

{v_fea}

feature liga {{
    lookup prog_h_full_liga;
    lookup prog_v_liga;
}} liga;

feature ss01 {{
    featureNames {{
        name "Show percentage label inside the bar";
    }};
    lookup prog_h_full_label;
}} ss01;
"""


def _build_master(params, feature_code):
    glyph_data = {}
    draw_base_glyphs(glyph_data)
    draw_progress_h_glyphs(glyph_data, params)
    draw_progress_v_glyphs(glyph_data, params)
    return build_font(
        glyph_data=glyph_data,
        feature_code=feature_code,
        family_name=FAMILY_NAME,
    )


def main():
    start = time.time()
    variable_dir = os.path.join(PROJECT_ROOT, "fonts", "variable")
    ttf_dir = os.path.join(PROJECT_ROOT, "fonts", "ttf")
    woff2_dir = os.path.join(PROJECT_ROOT, "fonts", "webfonts")

    print("ProgressType Build")
    print("=" * 50)

    axes_config = [
        ("RADI", "Radius",   0,   0, 210),
        ("wdth", "Width",   50, 100, 150),
        ("wght", "Weight", 100, 400, 900),
    ]

    feature_code = _feature_code()

    masters = []
    for i, (wdth, wght, rad, h_w, h_b, h_r, v_w, v_b, v_r) in enumerate(AXIS_MASTERS):
        params = params_for_master(h_w, h_b, h_r, v_w, v_b, v_r)
        print(f"  Building master {i+1}/{len(AXIS_MASTERS)} (wdth={wdth}, wght={wght}, RAD={rad})...")
        master_font = _build_master(params, feature_code)
        masters.append((master_font, {"Width": wdth, "Weight": wght, "Radius": rad}))

    glyph_count = len(masters[0][0].getGlyphOrder())
    print(f"  Glyphs per master: {glyph_count}")

    fvar_instances = [
        (style, {"Width": wdth, "Weight": wght, "Radius": 0})
        for style, wdth, wght in NAMED_INSTANCES
    ]

    print("  Merging masters into variable font...")
    vf = build_variable_font(masters, axes_config, fvar_instances)

    print(f"  Exporting variable font...")
    export_font(vf, variable_dir, f"{FAMILY_NAME}[RADI,wdth,wght]")

    print(f"  Exporting static instances...")
    for style_name, wdth, wght in NAMED_INSTANCES:
        export_static_instance(
            vf,
            # Pin all three axes (including RADI=0) so the resulting font is
            # fully static. Without pinning RADI the instancer leaves fvar/
            # gvar/STAT/HVAR in place, which has been observed to crash
            # Chrome's GPU COLR rasteriser during repaint.
            location={"wght": wght, "wdth": wdth, "RADI": 0},
            output_dir=ttf_dir,
            basename=FAMILY_NAME,
            style_name=style_name,
            weight_class=wght,
            woff2_dir=woff2_dir,
        )

    print(f"  Exporting radius variants (Regular @ wdth=100)...")
    import copy
    from fontTools.varLib.instancer import instantiateVariableFont
    for variant_name, rad_value in [("Mid", 105), ("Pill", 210)]:
        static = instantiateVariableFont(
            copy.deepcopy(vf),
            {"wght": 400, "wdth": 100, "RADI": rad_value},
        )
        clean_static_glyphs(static)
        ps_name = f"{FAMILY_NAME}-{variant_name}"
        full_name = f"{FAMILY_NAME} {variant_name}"
        nt = static["name"]
        nt.names = [r for r in nt.names if r.platformID != 1]
        nt.setName(FAMILY_NAME, 1, 3, 1, 0x0409)
        nt.setName(variant_name, 2, 3, 1, 0x0409)
        nt.setName(full_name, 4, 3, 1, 0x0409)
        nt.setName(ps_name, 6, 3, 1, 0x0409)
        static["OS/2"].usWeightClass = 400
        ttf_path = os.path.join(ttf_dir, f"{ps_name}.ttf")
        static.save(ttf_path)
        print(f"    {ttf_path}")
        static.flavor = "woff2"
        woff2_path = os.path.join(woff2_dir, f"{ps_name}.woff2")
        static.save(woff2_path)
        print(f"    {woff2_path}")

    elapsed = time.time() - start
    print(f"\nBuild complete in {elapsed:.1f}s")
    print(f"Output:")
    print(f"  Variable: fonts/variable/")
    print(f"  Static TTF: fonts/ttf/")
    print(f"  Static WOFF2: fonts/webfonts/")


if __name__ == "__main__":
    main()
