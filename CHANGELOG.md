# Changelog

## 1.1 — unreleased

### Breaking

- **Multi-segment bars (`{h:NN,MM,...}`) removed.** Only single-segment
  `{h:NN}` and `{v:NN}` ligatures remain. Multi-segment relied on COLR/CPAL
  color layers; Chrome's Skia + DirectWrite GPU rasteriser crashes
  intermittently on COLR fonts on Windows
  ([skia 338390594](https://issues.skia.org/issues/338390594),
  [Mozilla 1933050](https://bugzilla.mozilla.org/show_bug.cgi?id=1933050)).
  Multi-segment can come back when browser font engines stabilise their
  color-font path.
- **COLR/CPAL tables removed.** Bars are now monochrome — tint via CSS
  `color`. Glyphs-per-font dropped 1751 → 522, build time 17s → 4s,
  WOFF2 sizes 27 KB → ~12 KB.

### Added

- **`RADI` variable axis** for outer-corner radius (0 = square, 210 = pill).
  Pre-rendered static instances `ProgressType-Mid` (RADI 105) and
  `ProgressType-Pill` (RADI 210) ship alongside the named-weight statics.
- **`ss01` stylistic set** — opt-in in-bar percentage label, knock-out style
  (digits punch through the bar revealing the page background). Enable via
  `font-feature-settings: 'ss01' 1;`. Includes a CSS container-query
  pattern in the preview for hiding the label below a usable bar width.
- Variable-font playground: `wdth` / `wght` / `RADI` sliders; bar size 2x;
  side-by-side bare and `ss01`-labeled examples.
- Repo link in the preview page header.

### Fixed

- **Variable-font master compatibility for vertical pill bars.** The fill
  rect's `fx0` / `fx1` were insetting by `v_bar_radius`, producing
  reversed-winding rectangles at pill (`fx0 > fx1`). varLib silently emitted
  zero gvar deltas and the bar collapsed to a rectangle at all RADI values.
  X bounds now inset by border alone; only Y bounds use the radius.
- **Float-epsilon at cardinal arc angles.** `math.cos(270°) ≈ 6e-17` rather
  than exactly 0 leaked into endpoint coordinates and broke
  `TTGlyphPen.closePath`'s auto-pop, which broke varLib master compat.
  Arc points now round to int.
- **Coincident-edge contours in `prog_h_full_track`.** The previous
  4-contour design (two end-caps + two strip rects) had abutting edges that
  tripped Skia GPU PathOps (skia 338390594) and crashed Chrome rendering.
  Replaced with a single 2-contour rect-with-hole shape.
- **Polyline arc rendering replaced with quadratic Béziers** via `qCurveTo`.
  Two quadratics per quarter arc gives ~0.3 % deviation from a true circle
  with far fewer points; GPU rasterisers handle one curve primitive much
  better than 8+ short line segments.
- **Variable-font residue in static instances.** `instantiateVariableFont`
  was leaving `fvar` / `gvar` / `STAT` / `HVAR` in static fonts because
  RADI wasn't pinned. Static exports now pin all three axes and drop STAT
  explicitly.

### Font hygiene

- STAT table declares the RADI axis with `Square` (elided default), `Mid`,
  `Pill` value records.
- Empty-glyph-at-GID-1 invariant verified (DirectWrite COLRv0 workaround).
- Name table populated with `nameID 4` (full name), `nameID 5` (version
  string), `nameID 6` (PostScript name), unique font identifier.
- OS/2: `ulCodePageRange1` (Latin-1, Latin-2, Mac Roman) + PANOSE
  (sans-text, normal-sans, book) set explicitly.
- Smart-dropout `prep` table added (standard 7-byte program).
- `ss01` stylistic set has a name-table description ("Show percentage label
  inside the bar") so font pickers display it.
- Ligature output glyphs declare a single placeholder caret in GDEF
  `LigCaretList` to satisfy fontbakery's `ligature_carets` check (OTS
  rejects `CaretCount=0` even though the OpenType spec arguably allows it).

### Validation

- All 12 shipped fonts pass `ots-sanitize` cleanly.
- fontbakery `check-universal`: 95 PASS / 1 FAIL / 5 WARN. The single FAIL
  (`opentype/monospace`) is a known false positive for our hybrid font —
  ASCII base glyphs are 500-wide (monospaced) while progress glyphs are
  intentionally wider; fontbakery's heuristic can't model the hybrid case.

### Infrastructure

- GitHub Pages workflow downloads release artifacts and publishes
  `dev/preview.html` (no longer rebuilds the font on Pages).
- Release workflow attaches every shipped font (variable + 11 static
  instances) tag-suffixed.

## 1.0 — 2026-05-09

Initial release.

- Variable OpenType font with `wdth` and `wght` axes.
- `{h:NN}` (single-segment fixed-width) and `{h:NN,MM,...}` (multi-segment
  stacked) horizontal bars; `{v:NN}` vertical bar.
- COLR/CPAL color layers with five named palettes (sequential, RAG,
  categorical, ocean, mono) plus per-segment colours via palette index.
- Nine named static instances (Thin → Black) at default width.
- IBM Plex Mono base glyphs for Latin Core coverage.
- GitHub Pages preview site published from the latest release.
