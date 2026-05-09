# Datatype Progress

A color, variable OpenType font that renders progress bars from text expressions.

```
{h:75}              single horizontal bar at 75%
{h:25,10,15}        stacked horizontal bar with 3 segments (50% total)
{h:10,10,10,10,10,10,10,10}   up to 8 segments
{v:75}              vertical bar at 75%
```

Built as a sibling project to [Datatype](../datatype/) — same idea, focused on progress indicators, with CPAL color palette support and variable `wght`/`wdth` axes.

## Syntax

| Pattern | Result |
| --- | --- |
| `{h:N}` | horizontal bar, N% (0..100) |
| `{h:N,M}` | stacked horizontal bar, segments N, M |
| `{h:N,M,...}` up to 8 | stacked with up to 8 positions |
| `{v:N}` | vertical bar, N% |

Vertical bars are single-segment only — multi-segment vertical isn't physically possible in inline text without a per-stack-position glyph explosion.

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
  font-family: 'DatatypeProgress';
  base-palette: 1;
}

.bar {
  font-family: 'DatatypeProgress', monospace;
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
    font-family: 'DatatypeProgress';
    src: url('DatatypeProgress[wdth,wght].woff2') format('woff2');
    font-weight: 100 900;
    font-stretch: 50% 150%;
  }
  .bar {
    font-family: 'DatatypeProgress', monospace;
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
make clean
```

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
  variable/              # Datatype Progress variable font
  ttf/                   # static instances per weight
  webfonts/              # static WOFF2 per weight
```

## Limitations & roadmap

- **Vertical multi-segment** — not supported (architectural).
- **Inline color codes** (`{h:25g,10b}`) — not implemented; ship-time decision was to use position-based palettes instead. Could be added later with an explosion in glyph count.
- **Animated/striped fill styles** — not implemented.

## License

OFL 1.1. Base glyphs derived from IBM Plex Mono (Copyright IBM, OFL 1.1).
