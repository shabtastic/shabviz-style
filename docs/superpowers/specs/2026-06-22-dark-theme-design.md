# Design: `theme` parameter for shabviz-style

**Date:** 2026-06-22
**Status:** Approved

## Summary

Add a `theme` string parameter (`"light"` / `"dark"` / `"black"`) to `setup()`, `apply_style()`, `palette()`, and `binary_palette()` in both the Python and R implementations. Default is `"light"` — fully backward-compatible with all existing code.

- `"light"` — white background, dark text (current behavior, unchanged)
- `"dark"` — near-black (`#1a1a1a`) background, light gray text; suitable for screen/presentation use
- `"black"` — pure black (`#000000`) background, white text; matches the TRI slide deck

## Motivation

Scientific figures are often embedded in dark-background slide decks (e.g., TRI). The current light-only theme requires manual rcParam overrides in every script. A first-class `theme` parameter gives users a single call to produce properly themed figures without per-file workarounds.

## Theme color table

| rcParam element | `"light"` | `"dark"` | `"black"` |
|---|---|---|---|
| figure/axes/savefig background | `white` | `#1a1a1a` | `#000000` |
| `text.color` | `#333333` | `#e0e0e0` | `#ffffff` |
| `axes.labelcolor`, `axes.titlecolor` | `#333333` | `#e0e0e0` | `#ffffff` |
| `axes.edgecolor`, `xtick.color`, `ytick.color` | `#333333` | `#666666` | `#888888` |
| `grid.color` | `#cccccc` | `#444444` | `#333333` |
| `legend.facecolor` | `white` | `#1a1a1a` | `#000000` |
| `legend.edgecolor` | `#cccccc` | `#666666` | `#888888` |
| `legend.frameon` | `True` | `True` | `True` |

Note: `legend.frameon` changes from `False` (current default) to `True` for all themes. On light this gives a subtle gray border; on dark/black the frame provides a background that keeps the legend readable over data lines.

## Palette sampling ranges

`"dark"` and `"black"` share one range table — their palette problem is identical (dark end of viridis family disappears into the background). The only difference between them is background hex value.

| cmap | light `(lo, hi)` | dark/black `(lo, hi)` |
|---|---|---|
| viridis | `(0.05, 0.92)` | `(0.30, 0.95)` |
| mako | `(0.20, 0.92)` | `(0.35, 0.95)` |
| rocket | `(0.20, 0.92)` | `(0.35, 0.95)` |
| crest | `(0.10, 0.92)` | `(0.30, 0.95)` |
| flare | `(0.10, 0.92)` | `(0.30, 0.95)` |
| cividis | `(0.05, 0.95)` | `(0.30, 0.95)` |

The shift skips the near-black low end of each colormap, which would be invisible against dark/black backgrounds.

## Colorblind safety tradeoff

Viridis and its cousins are colorblind-safe by design (perceptually uniform under deuteranopia, protanopia, and tritanopia). The dark/black range shift narrows the sampling window from ~0.87 to ~0.65 of the colormap span. This reduces perceptual separation between adjacent colors when N is large (6+ groups). For typical 2–5 group scientific figures this is acceptable, but users plotting 6+ categories on dark/black backgrounds should be aware that color discrimination is reduced. A future qualitative palette feature (outside this scope) would address the large-N case properly.

## API

### Python

```python
import shabviz_style as pf

pf.setup(theme="dark")            # near-black background
pf.setup(theme="black")           # pure black
pf.setup()                        # unchanged: light (default)
pf.setup(theme="dark", cmap="mako")

# Palette helpers also accept theme= for manual use
pf.palette(4, theme="dark")
pf.binary_palette(theme="black")
```

### R

```r
library(shabvizstyle)

setup(theme = "dark")
setup(theme = "black")
setup()                           # unchanged: light (default)

theme_shabviz(theme = "dark")     # for manual ggplot composition
palette_sv(4, theme = "dark")
binary_palette(theme = "black")
```

`rc_overrides` (Python) and additional `theme()` calls (R) still work on top of whatever theme is active.

## Files to change

### Python: `python/shabviz_style.py`

1. Add `_RANGE_DARK` dict alongside the existing `_DEFAULT_RANGE` (renamed to `_RANGE_LIGHT`).
2. Add `_THEME_COLORS` dict keyed by theme name, containing all background/text/spine/grid/legend values.
3. Update `_resolve_range(cmap, lo, hi)` to accept `theme` and pick the right range table.
4. Update `_build_rcparams(cmap, font, theme)` to inject background and text colors from `_THEME_COLORS`.
5. Add `theme: str = "light"` parameter to `apply_style()`, `setup()`, `palette()`, `binary_palette()`.
6. Update `__all__` to export `THEMES`.

### R: `r/R/palettes.R`

1. Add `.range_dark` list alongside the existing `.default_range` (renamed `.range_light`).
2. Update `.resolve_range(cmap, lo, hi, theme)` to pick the right table.
3. Add `theme = "light"` parameter to `palette_sv()` and `binary_palette()`.

### R: `r/R/theme.R`

1. Add `.theme_colors` list keyed by theme name.
2. Update `theme_shabviz(base_size, base_family, theme)` to inject background/text/legend colors from `.theme_colors`.
3. Add `theme = "light"` parameter to `setup()`.

## Backward compatibility

All new parameters default to `"light"`, which reproduces current behavior exactly. One minor behavior change: `legend.frameon` changes from `False` to `True` for the light theme (adding a subtle `#cccccc` border). This is a visible change but an improvement — users who prefer no frame can override with `rc_overrides={'legend.frameon': False}`.
