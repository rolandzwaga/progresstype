# ProgressType

A color, variable OpenType font that renders progress bars from text expressions.

```
{h:75}              single horizontal bar at 75%
{h:25,10,15}        stacked horizontal bar with 3 segments (50% total)
{h:10,10,10,10,10,10,10,10}   up to 8 segments
{v:75}              vertical bar at 75%
```

Built as a sibling project to [Datatype](../datatype/) — same idea, focused on progress indicators, with CPAL color palette support and variable `wght`/`wdth` axes.

## Syntax

| Pattern | Result | Visual |
| --- | --- | --- |
| `{h:N}` | horizontal bar, N% (0..100) | **fixed width** — N% colored fill, (100-N)% empty track on the right |
| `{h:N,M,...}` up to 8 | stacked horizontal bar | **variable width** — bar grows with the sum of segment values |
| `{v:N}` | vertical bar, N% | **fixed cell** — fill grows from the bottom |

The visual difference between single and multi-segment is intentional and reflects two distinct use cases:

- **Single `{h:N}` and `{v:N}`** — show progress *against a known whole*. The bar is a fixed-size container; the fill is N% of it. Empty space is meaningful (it's "the rest").
- **Multi `{h:N,M,...}`** — show *proportional breakdowns*. Segment widths are absolute (in percent of a reference width), and the bar's total visual width is the sum. There is no implicit "remainder" — if you want one, manually pad the values to total 100% (e.g. `{h:25,10,15,50}` with the trailing position styled as a track-color via `font-palette` overrides).

The architectural reason for this split: OpenType GSUB cannot perform arithmetic, so a renderer cannot compute "100 - sum(segments)" to draw the remainder. Multi-segment fixed-width would require pre-baking every possible value combination — impractical at 1% × 8 segments.

Vertical bars are single-segment only.

## Color (position-based CPAL)

Each segment's color is determined by its **position** in the list (1st = palette index 1, 2nd = palette index 2, …). The font ships with five palettes:

| Palette | Use case | Index |
| --- | --- | --- |
| `sequential` | gradient of one hue (ranking, ordinal) | 0 |
| `rag` | red/amber/green status | 1 |
| `categorical` | distinct hues for unrelated categories | 2 |
| `ocean` | blue gradient | 3 |
| `mono` | foreground-only (no color variation) | 4 |

Switch palettes via CSS:

```css
@font-palette-values --rag {
  font-family: 'ProgressType';
  base-palette: 1;
}

.bar {
  font-family: 'ProgressType', monospace;
  font-feature-settings: 'liga' 1, 'calt' 1;
  font-palette: --rag;
}
```

Renderers without COLR/CPAL support fall back to a monochrome composite (track outline + segments rendered in foreground color).

## Variable axes

| Axis | Tag | Range | Effect |
| --- | --- | --- | --- |
| Weight | `wght` | 100..900 | track border thickness (Thin = hairline, Black = chunky) |
| Width | `wdth` | 50..150 | overall bar length |

Static instances (TTF + WOFF2) are also exported for each weight at width 100.

## Usage

```html
<style>
  @font-face {
    font-family: 'ProgressType';
    src: url('ProgressType[wdth,wght].woff2') format('woff2');
    font-weight: 100 900;
    font-stretch: 50% 150%;
  }
  .bar {
    font-family: 'ProgressType', monospace;
    font-feature-settings: 'liga' 1, 'calt' 1;
  }
</style>

<p class="bar">Status: {h:45,30,25}</p>
```

`calt` must be enabled for multi-segment to work — it carries the position-tagging chain rules. `liga` carries the simpler vertical and single-segment direct ligatures.

## Build

```sh
make venv      # create .venv and install fontTools
make build     # writes fonts/{variable,ttf,webfonts}/
make serve     # serves dev/preview.html at http://localhost:8080/
make clean
```

The dev server is needed because `dev/preview.html` references `../fonts/...` —
serving from `dev/` directly with `python -m http.server` can't reach above
the served root. `make serve` serves from project root and routes `/` → preview.html.

## Project layout

```
sources/
  config.py              # font metrics, bar geometry, axis masters, palettes
  build.py               # build orchestrator
  font_builder.py        # FontBuilder + COLR/CPAL + varLib + STAT
  export.py              # TTF/WOFF2 writers
  glyphs/
    base_imported.py     # Latin Core (IBM Plex Mono, OFL)
    progress_h.py        # opener/closer/segment glyphs + multi-segment GSUB pipeline
    progress_v.py        # vertical single-segment glyphs + ligature
  imported_glyphs.pkl    # IBM Plex Mono outline data
dev/
  preview.html           # specimen page with palette swap demos + axis sliders
fonts/
  variable/              # ProgressType variable font
  ttf/                   # static instances per weight
  webfonts/              # static WOFF2 per weight
```

## Limitations & roadmap

- **Vertical multi-segment** — not supported (architectural).
- **Inline color codes** (`{h:25g,10b}`) — not implemented; ship-time decision was to use position-based palettes instead. Could be added later with an explosion in glyph count.
- **Animated/striped fill styles** — not implemented.

## License

OFL 1.1. Base glyphs derived from IBM Plex Mono (Copyright IBM, OFL 1.1).
