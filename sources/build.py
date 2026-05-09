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
    draw_progress_h_glyphs, colr_layers_h,
    generate_progress_h_feature_code, generate_progress_h_full_liga_code,
    progress_h_calt_lookups,
)
from sources.glyphs.progress_v import (
    draw_progress_v_glyphs, colr_layers_v, generate_progress_v_feature_code,
)
from sources.font_builder import (
    build_font, build_variable_font, export_static_instance,
)
from sources.export import export_font


def _feature_code():
    h_full_fea = generate_progress_h_full_liga_code()
    h_fea = generate_progress_h_feature_code()
    v_fea = generate_progress_v_feature_code()

    # liga: direct ligatures for fixed-width single-segment {h:NN} and {v:NN}.
    # calt: multi-stage pipeline for stacked horizontal {h:NN,MM,...}.
    # The liga direct match is longer than the calt open ligature ({h:NN} vs {h:),
    # so single-segment input always resolves to the fixed-width baked glyph.
    h_calt_lookups = progress_h_calt_lookups()
    h_calt_block = "\n".join(f"    lookup {name};" for name in h_calt_lookups)

    return f"""
{h_full_fea}

{h_fea}

{v_fea}

feature liga {{
    lookup prog_h_full_liga;
    lookup prog_v_liga;
}} liga;

feature calt {{
{h_calt_block}
}} calt;
"""


def _build_master(params, feature_code, color_layers):
    glyph_data = {}
    draw_base_glyphs(glyph_data)
    draw_progress_h_glyphs(glyph_data, params)
    draw_progress_v_glyphs(glyph_data, params)
    return build_font(
        glyph_data=glyph_data,
        feature_code=feature_code,
        color_layers=color_layers,
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
    color_layers = {**colr_layers_h(), **colr_layers_v()}

    masters = []
    for i, (wdth, wght, rad, h_w, h_b, h_r, v_w, v_b, v_r) in enumerate(AXIS_MASTERS):
        params = params_for_master(h_w, h_b, h_r, v_w, v_b, v_r)
        print(f"  Building master {i+1}/{len(AXIS_MASTERS)} (wdth={wdth}, wght={wght}, RAD={rad})...")
        master_font = _build_master(params, feature_code, color_layers)
        masters.append((master_font, {"Width": wdth, "Weight": wght, "Radius": rad}))

    glyph_count = len(masters[0][0].getGlyphOrder())
    print(f"  Glyphs per master: {glyph_count}")

    fvar_instances = [
        (style, {"Width": wdth, "Weight": wght})
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
            location={"wght": wght, "wdth": wdth},
            output_dir=ttf_dir,
            basename=FAMILY_NAME,
            style_name=style_name,
            weight_class=wght,
            woff2_dir=woff2_dir,
        )

    elapsed = time.time() - start
    print(f"\nBuild complete in {elapsed:.1f}s")
    print(f"Output:")
    print(f"  Variable: fonts/variable/")
    print(f"  Static TTF: fonts/ttf/")
    print(f"  Static WOFF2: fonts/webfonts/")


if __name__ == "__main__":
    main()
