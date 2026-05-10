# ProgressType

A monochrome variable OpenType font that renders progress bars from text expressions.

```
{h:75}    horizontal bar at 75%
{v:75}    vertical bar at 75%
```

Inspired by [Datatype](https://github.com/franktisellano/datatype) — same idea, focused on progress indicators, with variable `wght` / `wdth` / `RADI` axes.

## Syntax

| Pattern | Result |
| --- | --- |
| `{h:N}` | horizontal bar, N% (0..100). Fixed-width container; N% colored fill, (100-N)% empty track on the right. |
| `{v:N}` | vertical bar, N%. Fill grows from the bottom. |

That's the whole syntax. Multi-segment stacked bars (e.g. `{h:25,10,15}`) used to exist via COLR/CPAL color layers but were removed because Chrome's Skia + DirectWrite GPU rasteriser crashes intermittently on COLR fonts on Windows (skia issue 338390594, Mozilla bug 1933050). They can come back when browser font engines stabilise their color-font path.

## Tinting

Set `color` on the bar element:

```css
.bar {
  font-family: 'ProgressType', monospace;
  font-feature-settings: 'liga' 1;
  color: #ef4444;        /* tint with any CSS color */
}
```

```html
<p class="bar">Disk: {h:91}</p>
```

## Variable axes

| Axis | Tag | Range | Effect |
| --- | --- | --- | --- |
| Width | `wdth` | 50..150 | overall bar length |
| Weight | `wght` | 100..900 | track border thickness (Thin = hairline, Black = chunky) |
| Radius | `RADI` | 0..210 | outer-corner radius (0 = square, 210 = pill) |

Static instances are exported for each named weight (Thin, Light, Regular, Medium, SemiBold, Bold, ExtraBold, Black) at default width and zero radius. Two extra static instances `ProgressType-Mid` (RADI 105) and `ProgressType-Pill` (RADI 210) ship for convenience.

## Usage

```html
<style>
  @font-face {
    font-family: 'ProgressType';
    src: url('ProgressType[RADI,wdth,wght].woff2') format('woff2');
    font-weight: 100 900;
    font-stretch: 50% 150%;
  }
  .bar {
    font-family: 'ProgressType', monospace;
    font-feature-settings: 'liga' 1;
    color: #6366f1;
    /* font-variation-settings: 'RADI' 210; — pill ends */
  }
</style>

<p class="bar">Disk usage: {h:91}</p>
```

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
  config.py              # font metrics, bar geometry, axis masters
  build.py               # build orchestrator
  font_builder.py        # FontBuilder + varLib + STAT
  export.py              # TTF/WOFF2 writers
  glyphs/
    base_imported.py     # Latin Core (IBM Plex Mono, OFL)
    progress_h.py        # horizontal {h:NN} bar glyphs + ligature
    progress_v.py        # vertical {v:NN} bar glyphs + ligature
  imported_glyphs.pkl    # IBM Plex Mono outline data
dev/
  preview.html           # specimen page
fonts/
  variable/              # ProgressType variable font
  ttf/                   # static instances per weight
  webfonts/              # static WOFF2 per weight
```

## Limitations & roadmap

- **Multi-segment / multi-colour stacked bars** — removed pending stable browser COLR support. Track skia issue [338390594](https://issues.skia.org/issues/338390594) and Mozilla bug [1933050](https://bugzilla.mozilla.org/show_bug.cgi?id=1933050).
- **Animated/striped fill styles** — not implemented.

## License

OFL 1.1. Base glyphs derived from IBM Plex Mono (Copyright IBM, OFL 1.1).
