# Dark/Black Theme Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `theme="light"/"dark"/"black"` parameter to `setup()`, `apply_style()`, `palette()`, and `binary_palette()` in both Python and R, with appropriate background/text colors and per-theme palette sampling ranges.

**Architecture:** A `_THEME_COLORS` dict (Python) / `.theme_colors` list (R) holds all background/text/legend rcParam values per theme. A `_RANGE_DARK` table (alongside the renamed `_RANGE_LIGHT`) holds shifted palette sampling ranges shared by both dark and black themes. All new parameters default to `"light"` for full backward compatibility.

**Tech Stack:** Python 3.9+, matplotlib ≥ 3.7, numpy, cycler, seaborn ≥ 0.12; R ≥ 4.0, ggplot2 ≥ 3.4.0, viridisLite, pytest (Python tests), testthat (R tests).

## Global Constraints

- `theme` defaults to `"light"` everywhere — existing call sites must not break
- `"dark"` and `"black"` share the same palette sampling range table
- `legend.frameon` is `True` for all three themes (change from current `False` default)
- Valid theme values: `"light"`, `"dark"`, `"black"` — raise `ValueError` for anything else
- All rcParam keys added to `_build_rcparams` must be present in all three themes

---

## File Map

| File | Change |
|---|---|
| `python/shabviz_style.py` | Rename `_DEFAULT_RANGE` → `_RANGE_LIGHT`, add `_RANGE_DARK`, add `_THEME_COLORS`, thread `theme` through `_resolve_range`, `_build_rcparams`, `apply_style`, `setup`, `palette`, `binary_palette` |
| `python/tests/test_shabviz_style.py` | Create: unit tests for Python changes |
| `r/R/palettes.R` | Rename `.default_range` → `.range_light`, add `.range_dark`, thread `theme` through `.resolve_range`, `palette_sv`, `binary_palette` |
| `r/R/theme.R` | Add `.theme_colors`, thread `theme` through `theme_shabviz`, `setup` |
| `r/tests/testthat/test-theme.R` | Create: unit tests for R changes |

---

## Task 1: Python — theme color table + palette ranges

**Files:**
- Modify: `python/shabviz_style.py`
- Create: `python/tests/test_shabviz_style.py`

**Interfaces:**
- Produces:
  - `_RANGE_LIGHT: dict[str, tuple[float, float]]` — per-cmap light sampling ranges
  - `_RANGE_DARK: dict[str, tuple[float, float]]` — per-cmap dark/black sampling ranges
  - `_THEME_COLORS: dict[str, dict[str, str]]` — per-theme rcParam color values
  - `_resolve_range(cmap: str, lo, hi, theme: str) -> tuple[float, float]`

- [ ] **Step 1: Create test file with failing tests for the data tables**

Create `python/tests/__init__.py` (empty) and `python/tests/test_shabviz_style.py`:

```python
import sys
sys.path.insert(0, 'python')

import pytest
import shabviz_style as pf


def test_range_light_has_all_cmaps():
    for cmap in pf.SEQUENTIAL_CMAPS:
        lo, hi = pf._resolve_range(cmap, None, None, 'light')
        assert 0 <= lo < hi <= 1


def test_range_dark_has_all_cmaps():
    for cmap in pf.SEQUENTIAL_CMAPS:
        lo, hi = pf._resolve_range(cmap, None, None, 'dark')
        assert 0 <= lo < hi <= 1


def test_dark_lo_greater_than_light_lo():
    # Dark range must start higher to skip the near-black end
    for cmap in pf.SEQUENTIAL_CMAPS:
        light_lo, _ = pf._resolve_range(cmap, None, None, 'light')
        dark_lo, _ = pf._resolve_range(cmap, None, None, 'dark')
        assert dark_lo > light_lo, f"{cmap}: dark lo {dark_lo} not > light lo {light_lo}"


def test_black_uses_same_range_as_dark():
    for cmap in pf.SEQUENTIAL_CMAPS:
        dark = pf._resolve_range(cmap, None, None, 'dark')
        black = pf._resolve_range(cmap, None, None, 'black')
        assert dark == black


def test_resolve_range_override():
    lo, hi = pf._resolve_range('viridis', 0.1, 0.8, 'dark')
    assert lo == 0.1 and hi == 0.8


def test_invalid_theme_raises():
    with pytest.raises(ValueError, match="theme"):
        pf._resolve_range('viridis', None, None, 'neon')


def test_theme_colors_keys():
    for theme in ('light', 'dark', 'black'):
        c = pf._THEME_COLORS[theme]
        for key in ('fig_bg', 'axes_bg', 'save_bg', 'text', 'spines',
                    'ticks', 'grid', 'legend_bg', 'legend_edge'):
            assert key in c, f"theme '{theme}' missing key '{key}'"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/shabnamhakimi/repos/shabviz-style
python -m pytest python/tests/test_shabviz_style.py -v 2>&1 | head -40
```

Expected: multiple failures including `AttributeError: module 'shabviz_style' has no attribute '_THEME_COLORS'`.

- [ ] **Step 3: Rename `_DEFAULT_RANGE` to `_RANGE_LIGHT` and add `_RANGE_DARK` + `_THEME_COLORS`**

In `python/shabviz_style.py`, replace the `_DEFAULT_RANGE` and `_FALLBACK_RANGE` block (lines 164–172) with:

```python
_VALID_THEMES = {'light', 'dark', 'black'}

_RANGE_LIGHT = {
    'viridis':  (0.05, 0.92),
    'mako':     (0.20, 0.92),
    'rocket':   (0.20, 0.92),
    'crest':    (0.10, 0.92),
    'flare':    (0.10, 0.92),
    'cividis':  (0.05, 0.95),
}
_RANGE_DARK = {
    'viridis':  (0.30, 0.95),
    'mako':     (0.35, 0.95),
    'rocket':   (0.35, 0.95),
    'crest':    (0.30, 0.95),
    'flare':    (0.30, 0.95),
    'cividis':  (0.30, 0.95),
}
_FALLBACK_RANGE = (0.05, 0.92)
_FALLBACK_RANGE_DARK = (0.30, 0.95)

_THEME_COLORS = {
    'light': dict(
        fig_bg='white',    axes_bg='white',    save_bg='white',
        text='#333333',    spines='#333333',   ticks='#333333',
        grid='#cccccc',    legend_bg='white',  legend_edge='#cccccc',
    ),
    'dark': dict(
        fig_bg='#1a1a1a',  axes_bg='#1a1a1a',  save_bg='#1a1a1a',
        text='#e0e0e0',    spines='#666666',   ticks='#666666',
        grid='#444444',    legend_bg='#1a1a1a', legend_edge='#666666',
    ),
    'black': dict(
        fig_bg='#000000',  axes_bg='#000000',  save_bg='#000000',
        text='#ffffff',    spines='#888888',   ticks='#888888',
        grid='#333333',    legend_bg='#000000', legend_edge='#888888',
    ),
}
```

- [ ] **Step 4: Update `_resolve_range` to accept `theme`**

Replace the existing `_resolve_range` function:

```python
def _resolve_range(cmap: str, lo, hi, theme: str = 'light'):
    if theme not in _VALID_THEMES:
        raise ValueError(f"theme must be one of {sorted(_VALID_THEMES)!r}, got {theme!r}")
    range_table = _RANGE_LIGHT if theme == 'light' else _RANGE_DARK
    fallback = _FALLBACK_RANGE if theme == 'light' else _FALLBACK_RANGE_DARK
    default_lo, default_hi = range_table.get(cmap, fallback)
    return (default_lo if lo is None else lo,
            default_hi if hi is None else hi)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd /Users/shabnamhakimi/repos/shabviz-style
python -m pytest python/tests/test_shabviz_style.py -v
```

Expected: all 8 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add python/shabviz_style.py python/tests/__init__.py python/tests/test_shabviz_style.py
git commit -m "feat(python): add _RANGE_DARK, _THEME_COLORS, theme-aware _resolve_range"
```

---

## Task 2: Python — thread `theme` through rcParams and public API

**Files:**
- Modify: `python/shabviz_style.py`
- Modify: `python/tests/test_shabviz_style.py`

**Interfaces:**
- Consumes:
  - `_THEME_COLORS: dict[str, dict[str, str]]` (Task 1)
  - `_resolve_range(cmap, lo, hi, theme) -> tuple[float, float]` (Task 1)
- Produces:
  - `_build_rcparams(cmap: str, font: str, theme: str) -> dict`
  - `apply_style(cmap, font, theme, rc_overrides) -> None`
  - `setup(cmap, font, auto_install, rc_overrides, verbose, theme) -> None`
  - `palette(n, ordered, cmap, lo, hi, theme) -> list`
  - `binary_palette(cmap, positions, theme) -> list`

- [ ] **Step 1: Add failing tests for the public API**

Append to `python/tests/test_shabviz_style.py`:

```python
import matplotlib as mpl
from cycler import cycler


def test_setup_light_background():
    pf.setup(theme='light')
    assert mpl.rcParams['figure.facecolor'] == 'white'
    assert mpl.rcParams['axes.facecolor'] == 'white'


def test_setup_dark_background():
    pf.setup(theme='dark')
    assert mpl.rcParams['figure.facecolor'] == '#1a1a1a'
    assert mpl.rcParams['axes.facecolor'] == '#1a1a1a'


def test_setup_black_background():
    pf.setup(theme='black')
    assert mpl.rcParams['figure.facecolor'] == '#000000'
    assert mpl.rcParams['axes.facecolor'] == '#000000'


def test_setup_dark_text_color():
    pf.setup(theme='dark')
    assert mpl.rcParams['text.color'] == '#e0e0e0'
    assert mpl.rcParams['axes.labelcolor'] == '#e0e0e0'


def test_setup_black_text_color():
    pf.setup(theme='black')
    assert mpl.rcParams['text.color'] == '#ffffff'


def test_setup_legend_frameon_all_themes():
    for theme in ('light', 'dark', 'black'):
        pf.setup(theme=theme)
        assert mpl.rcParams['legend.frameon'] is True, f"legend.frameon False for {theme}"


def test_setup_default_is_light():
    pf.setup()
    assert mpl.rcParams['figure.facecolor'] == 'white'


def test_setup_invalid_theme_raises():
    with pytest.raises(ValueError, match="theme"):
        pf.setup(theme='neon')


def test_palette_dark_lo_shifted():
    light_colors = pf.palette(2, theme='light')
    dark_colors = pf.palette(2, theme='dark')
    # Colors should differ — dark range is shifted
    assert light_colors != dark_colors


def test_palette_black_equals_dark():
    dark_colors = pf.palette(4, theme='dark')
    black_colors = pf.palette(4, theme='black')
    assert dark_colors == black_colors


def test_binary_palette_dark():
    pair = pf.binary_palette(theme='dark')
    assert len(pair) == 2


def test_apply_style_rc_overrides_still_work():
    pf.apply_style(theme='dark', rc_overrides={'lines.linewidth': 3.0})
    assert mpl.rcParams['lines.linewidth'] == 3.0
```

- [ ] **Step 2: Run tests to verify new tests fail**

```bash
cd /Users/shabnamhakimi/repos/shabviz-style
python -m pytest python/tests/test_shabviz_style.py -v 2>&1 | tail -20
```

Expected: new tests fail with `TypeError: setup() got an unexpected keyword argument 'theme'`.

- [ ] **Step 3: Update `_build_rcparams` to accept and apply `theme`**

Replace the existing `_build_rcparams` function signature and color-related keys:

```python
def _build_rcparams(cmap: str = 'viridis', font: str = 'Inter',
                    theme: str = 'light'):
    if theme not in _VALID_THEMES:
        raise ValueError(f"theme must be one of {sorted(_VALID_THEMES)!r}, got {theme!r}")
    c = _THEME_COLORS[theme]
    cycle_colors = palette(6, ordered=False, cmap=cmap, theme=theme)

    fallbacks = [font, 'Inter', 'Helvetica Neue', 'Helvetica', 'Arial', 'DejaVu Sans']
    seen = set()
    sans_list = [f for f in fallbacks if not (f in seen or seen.add(f))]

    return {
        # --- Font ---
        'font.family':      'sans-serif',
        'font.sans-serif':  sans_list,
        'font.size':        11,
        'font.weight':      'normal',
        'mathtext.fontset': 'stixsans',

        # --- Figure ---
        'figure.figsize':     (6.5, 4.5),
        'figure.dpi':         110,
        'figure.facecolor':   c['fig_bg'],
        'figure.titlesize':   14,
        'figure.titleweight': 'medium',

        # --- Save / export ---
        'savefig.dpi':        300,
        'savefig.bbox':       'tight',
        'savefig.pad_inches': 0.05,
        'savefig.facecolor':  c['save_bg'],
        'pdf.fonttype':       42,
        'ps.fonttype':        42,
        'svg.fonttype':       'none',

        # --- Axes ---
        'axes.titlesize':    13,
        'axes.titleweight':  'medium',
        'axes.titlepad':     10,
        'axes.titlecolor':   c['text'],
        'axes.labelsize':    11,
        'axes.labelpad':     6,
        'axes.labelweight':  'normal',
        'axes.labelcolor':   c['text'],
        'axes.spines.top':   False,
        'axes.spines.right': False,
        'axes.linewidth':    0.8,
        'axes.edgecolor':    c['spines'],
        'axes.facecolor':    c['axes_bg'],

        # --- Text ---
        'text.color':        c['text'],

        # --- Ticks ---
        'xtick.labelsize':   10,
        'ytick.labelsize':   10,
        'xtick.direction':   'out',
        'ytick.direction':   'out',
        'xtick.major.size':  4,
        'ytick.major.size':  4,
        'xtick.major.width': 0.8,
        'ytick.major.width': 0.8,
        'xtick.minor.size':  2,
        'ytick.minor.size':  2,
        'xtick.color':       c['ticks'],
        'ytick.color':       c['ticks'],

        # --- Grid ---
        'axes.grid':      False,
        'grid.linewidth': 0.5,
        'grid.alpha':     0.3,
        'grid.color':     c['grid'],

        # --- Lines & patches ---
        'lines.linewidth':       1.8,
        'lines.markersize':      6,
        'lines.solid_capstyle':  'round',
        'lines.solid_joinstyle': 'round',
        'patch.edgecolor':       'none',
        'patch.linewidth':       0.5,

        # --- Legend ---
        'legend.fontsize':       10,
        'legend.title_fontsize': 10,
        'legend.frameon':        True,
        'legend.facecolor':      c['legend_bg'],
        'legend.edgecolor':      c['legend_edge'],
        'legend.borderpad':      0.4,
        'legend.handlelength':   1.5,
        'legend.handletextpad':  0.6,
        'legend.columnspacing':  1.4,

        # --- Color ---
        'image.cmap':      cmap,
        'axes.prop_cycle': cycler('color', cycle_colors),
    }
```

- [ ] **Step 4: Update `apply_style` to accept `theme`**

Replace the existing `apply_style` function:

```python
def apply_style(cmap: str = 'viridis', font: str = 'Inter',
                theme: str = 'light', rc_overrides: dict = None):
    """Apply rcParams without touching font installation."""
    rc = _build_rcparams(cmap=cmap, font=font, theme=theme)
    if rc_overrides:
        rc.update(rc_overrides)
    plt.rcParams.update(rc)
```

- [ ] **Step 5: Update `setup` to accept `theme`**

Replace the existing `setup` function signature and body:

```python
def setup(cmap: str = 'viridis', font: str = 'Inter',
          auto_install: bool = True, rc_overrides: dict = None,
          verbose: bool = False, theme: str = 'light') -> None:
    """Set up the figure style: register the font (optional) and apply rcParams.

    Parameters
    ----------
    cmap : str, default 'viridis'
        Sequential colormap.
    font : str, default 'Inter'
        Sans-serif body font.
    auto_install : bool, default True
        Whether to attempt downloading and registering the font.
    rc_overrides : dict, optional
        Extra rcParams to apply on top of the defaults.
    verbose : bool, default False
        Print status messages.
    theme : str, default 'light'
        Color theme. One of 'light', 'dark', 'black'.
        'light' — white background, dark text (default).
        'dark'  — near-black (#1a1a1a) background, light gray text.
        'black' — pure black background, white text (TRI slide deck).
    """
    if auto_install:
        ok = install_font(font)
        if verbose:
            msg = (f'{font} registered.' if ok
                   else f'{font} not available; using fallback sans-serif.')
            print(f'[shabviz_style] {msg}')

    apply_style(cmap=cmap, font=font, theme=theme, rc_overrides=rc_overrides)
    if verbose:
        print(f'[shabviz_style] Style applied (cmap={cmap}, font={font}, theme={theme}).')
```

- [ ] **Step 6: Update `palette` and `binary_palette` to accept `theme`**

Replace both functions:

```python
def palette(n: int, ordered: bool = False, cmap: str = 'viridis',
            lo: float = None, hi: float = None, theme: str = 'light'):
    """Return n perceptually distinct colors from a viridis-family colormap.

    Parameters
    ----------
    n : int
        Number of colors.
    ordered : bool, default False
        If True, return colors in colormap order (ordinal data).
    cmap : str, default 'viridis'
        Any sequential matplotlib/seaborn colormap.
    lo, hi : float, optional
        Sample range override. Defaults are tuned per-cmap and per-theme.
    theme : str, default 'light'
        One of 'light', 'dark', 'black'. Selects the sampling range table.
    """
    if n < 1:
        raise ValueError('n must be >= 1')

    cm = mpl.colormaps[cmap]
    lo, hi = _resolve_range(cmap, lo, hi, theme)

    if n == 1:
        return [cm(0.5)]

    positions = np.linspace(lo, hi, n)
    colors = [cm(p) for p in positions]

    if not ordered:
        colors = _maxdist_reorder(colors)
    return colors


def binary_palette(cmap: str = 'viridis', positions=None,
                   theme: str = 'light'):
    """High-contrast binary pair from a viridis-family colormap.

    Parameters
    ----------
    cmap : str, default 'viridis'
        Colormap name.
    positions : tuple of (lo, hi), optional
        Explicit sample positions. None uses per-cmap/per-theme defaults.
    theme : str, default 'light'
        One of 'light', 'dark', 'black'. Used when positions is None.
    """
    cm = mpl.colormaps[cmap]
    if positions is None:
        positions = _resolve_range(cmap, None, None, theme)
    return [cm(positions[0]), cm(positions[1])]
```

- [ ] **Step 7: Update `__all__`**

Replace the `__all__` list:

```python
__all__ = [
    'setup', 'apply_style', 'install_font',
    'palette', 'binary_palette',
    'SEQUENTIAL_CMAPS', 'DIVERGING_CMAPS',
    '_THEME_COLORS', '_RANGE_LIGHT', '_RANGE_DARK', '_resolve_range',
]
```

- [ ] **Step 8: Run all tests**

```bash
cd /Users/shabnamhakimi/repos/shabviz-style
python -m pytest python/tests/test_shabviz_style.py -v
```

Expected: all tests PASS.

- [ ] **Step 9: Commit**

```bash
git add python/shabviz_style.py python/tests/test_shabviz_style.py
git commit -m "feat(python): add theme parameter to setup/apply_style/palette/binary_palette"
```

---

## Task 3: R — palette range tables and `theme` parameter

**Files:**
- Modify: `r/R/palettes.R`
- Create: `r/tests/testthat/test-theme.R`

**Interfaces:**
- Produces:
  - `.range_light` — named list of (lo, hi) pairs per cmap
  - `.range_dark` — named list of shifted (lo, hi) pairs per cmap
  - `.valid_themes` — character vector `c("light", "dark", "black")`
  - `.resolve_range(cmap, lo, hi, theme)` — returns length-2 numeric
  - `palette_sv(n, ordered, cmap, lo, hi, theme)` — returns character vector
  - `binary_palette(cmap, positions, theme)` — returns length-2 character vector

- [ ] **Step 1: Create test file with failing tests**

Create `r/tests/testthat/test-theme.R`:

```r
library(testthat)
library(shabvizstyle)

test_that("light range lo is lower than dark range lo for all cmaps", {
  cmaps <- c("viridis", "mako", "rocket", "crest", "flare", "cividis")
  for (cmap in cmaps) {
    light_lo <- shabvizstyle:::.resolve_range(cmap, NULL, NULL, "light")[1]
    dark_lo  <- shabvizstyle:::.resolve_range(cmap, NULL, NULL, "dark")[1]
    expect_true(dark_lo > light_lo,
      label = paste(cmap, ": dark lo", dark_lo, "not > light lo", light_lo))
  }
})

test_that("black uses same range as dark", {
  cmaps <- c("viridis", "mako", "rocket", "crest", "flare", "cividis")
  for (cmap in cmaps) {
    dark  <- shabvizstyle:::.resolve_range(cmap, NULL, NULL, "dark")
    black <- shabvizstyle:::.resolve_range(cmap, NULL, NULL, "black")
    expect_equal(dark, black)
  }
})

test_that("invalid theme raises error", {
  expect_error(shabvizstyle:::.resolve_range("viridis", NULL, NULL, "neon"),
               regexp = "theme")
})

test_that("resolve_range respects lo/hi override", {
  result <- shabvizstyle:::.resolve_range("viridis", 0.1, 0.8, "dark")
  expect_equal(result, c(0.1, 0.8))
})

test_that("palette_sv returns different colors for light vs dark", {
  light_cols <- palette_sv(2, theme = "light")
  dark_cols  <- palette_sv(2, theme = "dark")
  expect_false(identical(light_cols, dark_cols))
})

test_that("palette_sv dark and black return same colors", {
  dark_cols  <- palette_sv(4, theme = "dark")
  black_cols <- palette_sv(4, theme = "black")
  expect_identical(dark_cols, black_cols)
})

test_that("binary_palette returns length-2 for all themes", {
  for (theme in c("light", "dark", "black")) {
    result <- binary_palette(theme = theme)
    expect_length(result, 2)
  }
})

test_that("palette_sv default theme is light", {
  default_cols <- palette_sv(2)
  light_cols   <- palette_sv(2, theme = "light")
  expect_identical(default_cols, light_cols)
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/shabnamhakimi/repos/shabviz-style/r
Rscript -e "testthat::test_dir('tests/testthat', reporter = 'progress')" 2>&1 | head -30
```

Expected: errors including `could not find function ".resolve_range"`.

- [ ] **Step 3: Update `r/R/palettes.R`**

Replace the entire file:

```r
.valid_themes <- c("light", "dark", "black")

## Per-cmap default sample range — light backgrounds.
.range_light <- list(
  viridis = c(0.05, 0.92),
  mako    = c(0.20, 0.92),
  rocket  = c(0.20, 0.92),
  crest   = c(0.10, 0.92),
  flare   = c(0.10, 0.92),
  cividis = c(0.05, 0.95)
)

## Shifted range for dark/black backgrounds — avoids near-black low end.
.range_dark <- list(
  viridis = c(0.30, 0.95),
  mako    = c(0.35, 0.95),
  rocket  = c(0.35, 0.95),
  crest   = c(0.30, 0.95),
  flare   = c(0.30, 0.95),
  cividis = c(0.30, 0.95)
)

.fallback_range_light <- c(0.05, 0.92)
.fallback_range_dark  <- c(0.30, 0.95)

`%||%` <- function(a, b) if (is.null(a)) b else a

.resolve_range <- function(cmap, lo = NULL, hi = NULL, theme = "light") {
  if (!theme %in% .valid_themes) {
    stop(sprintf("theme must be one of %s, got '%s'",
                 paste(shQuote(.valid_themes), collapse = ", "), theme))
  }
  range_table <- if (theme == "light") .range_light else .range_dark
  fallback    <- if (theme == "light") .fallback_range_light else .fallback_range_dark
  default     <- range_table[[cmap]] %||% fallback
  c(if (is.null(lo)) default[1] else lo,
    if (is.null(hi)) default[2] else hi)
}

## Reorder so result starts with both endpoints (max contrast for binary use),
## then fills in by greedy max-min-distance.
.maxdist_reorder <- function(items) {
  n <- length(items)
  if (n <= 2) return(items)
  out <- c(1L, n)
  while (length(out) < n) {
    candidates <- setdiff(seq_len(n), out)
    dists <- vapply(candidates, function(c) min(abs(c - out)), numeric(1))
    out <- c(out, candidates[which.max(dists)])
  }
  items[out]
}

.cmap_function <- function(cmap) {
  switch(cmap,
    viridis = viridisLite::viridis,
    mako    = viridisLite::mako,
    rocket  = viridisLite::rocket,
    plasma  = viridisLite::plasma,
    inferno = viridisLite::inferno,
    magma   = viridisLite::magma,
    cividis = viridisLite::cividis,
    crest   = viridisLite::viridis,
    flare   = viridisLite::rocket,
    stop(sprintf("Unknown cmap '%s'. Try one of: %s", cmap,
                 paste(names(.range_light), collapse = ", ")))
  )
}

#' n perceptually distinct colors from a viridis-family colormap
#'
#' @param n Number of colors.
#' @param ordered If TRUE, return colors in colormap order (ordinal data).
#' @param cmap Sequential colormap name.
#' @param lo,hi Sample range override. NULL uses per-cmap/per-theme defaults.
#' @param theme Color theme: "light", "dark", or "black". Selects the
#'   sampling range table. Default "light".
#' @return Character vector of hex color codes, length n.
#' @export
palette_sv <- function(n, ordered = FALSE, cmap = "viridis",
                       lo = NULL, hi = NULL, theme = "light") {
  if (n < 1) stop("n must be >= 1")

  fn  <- .cmap_function(cmap)
  rng <- .resolve_range(cmap, lo, hi, theme)

  if (n == 1) return(fn(1, begin = 0.5, end = 0.5))

  positions <- seq(rng[1], rng[2], length.out = n)
  colors    <- vapply(positions, function(p) fn(1, begin = p, end = p),
                      character(1))

  if (!ordered) colors <- .maxdist_reorder(colors)
  colors
}

#' High-contrast binary pair from a viridis-family colormap
#'
#' @param cmap Colormap name.
#' @param positions Length-2 numeric in [0,1]. NULL uses per-cmap/per-theme defaults.
#' @param theme Color theme: "light", "dark", or "black". Default "light".
#' @return Length-2 character vector of hex color codes.
#' @export
binary_palette <- function(cmap = "viridis", positions = NULL,
                           theme = "light") {
  fn <- .cmap_function(cmap)
  if (is.null(positions)) {
    positions <- .resolve_range(cmap, NULL, NULL, theme)
  }
  c(fn(1, begin = positions[1], end = positions[1]),
    fn(1, begin = positions[2], end = positions[2]))
}
```

- [ ] **Step 4: Run tests**

```bash
cd /Users/shabnamhakimi/repos/shabviz-style/r
Rscript -e "testthat::test_dir('tests/testthat', reporter = 'progress')"
```

Expected: all palette/range tests PASS.

- [ ] **Step 5: Commit**

```bash
git add r/R/palettes.R r/tests/testthat/test-theme.R
git commit -m "feat(r): add .range_dark, theme-aware .resolve_range, palette_sv/binary_palette theme param"
```

---

## Task 4: R — thread `theme` through `theme_shabviz` and `setup`

**Files:**
- Modify: `r/R/theme.R`
- Modify: `r/tests/testthat/test-theme.R`

**Interfaces:**
- Consumes:
  - `.valid_themes`, `.resolve_range` (Task 3)
- Produces:
  - `.theme_colors` — named list of color dicts per theme
  - `theme_shabviz(base_size, base_family, theme)` — returns ggplot2 theme object
  - `setup(cmap, font, auto_install, base_size, verbose, theme)` — returns invisibly

- [ ] **Step 1: Add failing tests for theme_shabviz and setup**

Append to `r/tests/testthat/test-theme.R`:

```r
test_that("theme_shabviz light has white background", {
  t <- theme_shabviz(theme = "light")
  expect_equal(t$plot.background$fill, "white")
  expect_equal(t$panel.background$fill, "white")
})

test_that("theme_shabviz dark has #1a1a1a background", {
  t <- theme_shabviz(theme = "dark")
  expect_equal(t$plot.background$fill, "#1a1a1a")
  expect_equal(t$panel.background$fill, "#1a1a1a")
})

test_that("theme_shabviz black has #000000 background", {
  t <- theme_shabviz(theme = "black")
  expect_equal(t$plot.background$fill, "#000000")
})

test_that("theme_shabviz dark has light text", {
  t <- theme_shabviz(theme = "dark")
  expect_equal(t$text$colour, "#e0e0e0")
})

test_that("theme_shabviz black has white text", {
  t <- theme_shabviz(theme = "black")
  expect_equal(t$text$colour, "#ffffff")
})

test_that("theme_shabviz default theme is light", {
  t_default <- theme_shabviz()
  t_light   <- theme_shabviz(theme = "light")
  expect_equal(t_default$plot.background$fill,
               t_light$plot.background$fill)
})

test_that("setup invalid theme raises error", {
  expect_error(setup(theme = "neon"), regexp = "theme")
})
```

- [ ] **Step 2: Run tests to verify new tests fail**

```bash
cd /Users/shabnamhakimi/repos/shabviz-style/r
Rscript -e "testthat::test_dir('tests/testthat', reporter = 'progress')" 2>&1 | tail -20
```

Expected: new tests fail with `unused argument (theme = "light")`.

- [ ] **Step 3: Update `r/R/theme.R`**

Replace the entire file:

```r
.theme_colors <- list(
  light = list(
    bg          = "white",
    text        = "#333333",
    axis_line   = "#333333",
    legend_bg   = "white",
    legend_edge = "#cccccc",
    strip_text  = "#333333"
  ),
  dark = list(
    bg          = "#1a1a1a",
    text        = "#e0e0e0",
    axis_line   = "#666666",
    legend_bg   = "#1a1a1a",
    legend_edge = "#666666",
    strip_text  = "#e0e0e0"
  ),
  black = list(
    bg          = "#000000",
    text        = "#ffffff",
    axis_line   = "#888888",
    legend_bg   = "#000000",
    legend_edge = "#888888",
    strip_text  = "#ffffff"
  )
)

## Font registry — mirror of shabviz_style._FONT_SOURCES.
.font_sources <- list(
  Inter = list(family = "Inter", google = "Inter"),
  `Source Sans 3` = list(family = "Source Sans 3", google = "Source Sans 3"),
  `IBM Plex Sans` = list(family = "IBM Plex Sans", google = "IBM Plex Sans")
)

#' Install Inter (or another registered font) via sysfonts/showtext
#'
#' @param name Font name from .font_sources. Default "Inter".
#' @return TRUE if the font is now available, FALSE otherwise.
#' @export
install_inter <- function(name = "Inter") {
  if (!name %in% names(.font_sources)) {
    warning(sprintf("Font '%s' is not in the registry.", name))
    return(FALSE)
  }

  if (!.font_available(name)) {
    if (!requireNamespace("sysfonts", quietly = TRUE) ||
        !requireNamespace("showtext", quietly = TRUE)) {
      message(
        "[shabvizstyle] To auto-install fonts, install the 'sysfonts' and ",
        "'showtext' packages:\n",
        "  install.packages(c('sysfonts', 'showtext'))\n",
        "Or install ", name, " system-wide and restart R."
      )
      return(FALSE)
    }
    google_name <- .font_sources[[name]]$google
    tryCatch({
      sysfonts::font_add_google(google_name, name)
      showtext::showtext_auto()
    }, error = function(e) {
      message(sprintf("[shabvizstyle] Could not install %s: %s",
                      name, conditionMessage(e)))
      return(FALSE)
    })
  }
  .font_available(name)
}

.font_available <- function(name) {
  in_system <- name %in% systemfonts::system_fonts()$family
  in_showtext <- if (requireNamespace("sysfonts", quietly = TRUE)) {
    name %in% sysfonts::font_families()
  } else FALSE
  in_system || in_showtext
}

#' shabviz ggplot2 theme
#'
#' @param base_size Base font size in points. Default 11.
#' @param base_family Font family. Default "" tries Inter then falls back.
#' @param theme Color theme: "light", "dark", or "black". Default "light".
#' @return A ggplot2 theme object.
#' @export
theme_shabviz <- function(base_size = 11, base_family = "",
                          theme = "light") {
  if (!theme %in% .valid_themes) {
    stop(sprintf("theme must be one of %s, got '%s'",
                 paste(shQuote(.valid_themes), collapse = ", "), theme))
  }
  c <- .theme_colors[[theme]]

  family <- if (identical(base_family, "")) {
    if (.font_available("Inter")) "Inter" else ""
  } else base_family

  ggplot2::theme_minimal(base_size = base_size, base_family = family) +
    ggplot2::theme(
      text = ggplot2::element_text(colour = c$text),
      plot.title = ggplot2::element_text(size = base_size * 1.18,
                                         face = "plain",
                                         margin = ggplot2::margin(b = 10)),
      plot.subtitle = ggplot2::element_text(size = base_size,
                                            colour = c$text),
      axis.title = ggplot2::element_text(size = base_size, colour = c$text),
      axis.text  = ggplot2::element_text(size = base_size * 0.9,
                                         colour = c$text),
      axis.line  = ggplot2::element_line(colour = c$axis_line, linewidth = 0.4),
      axis.ticks = ggplot2::element_line(colour = c$axis_line, linewidth = 0.4),
      axis.ticks.length = grid::unit(3, "pt"),

      panel.grid.major = ggplot2::element_blank(),
      panel.grid.minor = ggplot2::element_blank(),
      panel.background = ggplot2::element_rect(fill = c$bg, colour = NA),
      plot.background  = ggplot2::element_rect(fill = c$bg, colour = NA),

      legend.position   = "right",
      legend.background = ggplot2::element_rect(fill = c$legend_bg,
                                                colour = c$legend_edge),
      legend.key        = ggplot2::element_blank(),
      legend.title      = ggplot2::element_text(size = base_size * 0.9),
      legend.text       = ggplot2::element_text(size = base_size * 0.9),

      strip.background = ggplot2::element_blank(),
      strip.text = ggplot2::element_text(size = base_size,
                                         colour = c$strip_text,
                                         face = "plain"),

      plot.margin = ggplot2::margin(8, 8, 8, 8)
    )
}

#' Set up shabvizstyle: register theme, default scales, and font
#'
#' @param cmap Base colormap. Default "viridis".
#' @param font Body font. Default "Inter".
#' @param auto_install Whether to attempt auto-installing the font.
#' @param base_size Base font size in points.
#' @param verbose Print status messages.
#' @param theme Color theme: "light", "dark", or "black". Default "light".
#' @export
setup <- function(cmap = "viridis", font = "Inter",
                  auto_install = TRUE, base_size = 11,
                  verbose = FALSE, theme = "light") {
  if (!theme %in% .valid_themes) {
    stop(sprintf("theme must be one of %s, got '%s'",
                 paste(shQuote(.valid_themes), collapse = ", "), theme))
  }

  if (auto_install && font %in% names(.font_sources)) {
    ok <- install_inter(font)
    if (verbose) {
      message(sprintf("[shabvizstyle] %s",
        if (ok) sprintf("%s registered.", font)
        else sprintf("%s not available; using fallback sans-serif.", font)
      ))
    }
  }

  ggplot2::theme_set(theme_shabviz(base_size = base_size,
                                   base_family = if (.font_available(font)) font else "",
                                   theme = theme))

  options(
    ggplot2.discrete.colour = function() scale_colour_shabviz_d(cmap = cmap, theme = theme),
    ggplot2.discrete.fill   = function() scale_fill_shabviz_d(cmap = cmap, theme = theme),
    ggplot2.continuous.colour = function() scale_colour_shabviz_c(cmap = cmap),
    ggplot2.continuous.fill   = function() scale_fill_shabviz_c(cmap = cmap)
  )

  if (verbose) {
    message(sprintf("[shabvizstyle] Theme and scales applied (cmap=%s, font=%s, theme=%s).",
                    cmap, font, theme))
  }
  invisible(NULL)
}
```

- [ ] **Step 4: Update `r/R/scales.R` to pass `theme` to palette_sv**

In `r/R/scales.R`, add `theme = "light"` parameter to `scale_colour_shabviz_d` and `scale_fill_shabviz_d`:

```r
#' Discrete shabviz color scale
#' @param cmap Colormap name (default "viridis").
#' @param ordered If TRUE, colors are in colormap order.
#' @param lo,hi Sample range. NULL uses per-cmap/per-theme defaults.
#' @param theme Color theme: "light", "dark", or "black". Default "light".
#' @param ... Passed to ggplot2::discrete_scale().
#' @export
scale_colour_shabviz_d <- function(cmap = "viridis", ordered = FALSE,
                                   lo = NULL, hi = NULL,
                                   theme = "light", ...) {
  ggplot2::discrete_scale(
    aesthetics = "colour",
    scale_name = "shabviz_d",
    palette = function(n) palette_sv(n, ordered = ordered, cmap = cmap,
                                     lo = lo, hi = hi, theme = theme),
    ...
  )
}

#' @rdname scale_colour_shabviz_d
#' @export
scale_color_shabviz_d <- scale_colour_shabviz_d

#' Discrete shabviz fill scale
#' @inheritParams scale_colour_shabviz_d
#' @export
scale_fill_shabviz_d <- function(cmap = "viridis", ordered = FALSE,
                                 lo = NULL, hi = NULL,
                                 theme = "light", ...) {
  ggplot2::discrete_scale(
    aesthetics = "fill",
    scale_name = "shabviz_d",
    palette = function(n) palette_sv(n, ordered = ordered, cmap = cmap,
                                     lo = lo, hi = hi, theme = theme),
    ...
  )
}

#' Continuous shabviz color scale
#' @param cmap Colormap name.
#' @param ... Passed to ggplot2::scale_colour_gradientn().
#' @export
scale_colour_shabviz_c <- function(cmap = "viridis", ...) {
  fn <- .cmap_function(cmap)
  ggplot2::scale_colour_gradientn(colours = fn(256), ...)
}

#' @rdname scale_colour_shabviz_c
#' @export
scale_color_shabviz_c <- scale_colour_shabviz_c

#' Continuous shabviz fill scale
#' @inheritParams scale_colour_shabviz_c
#' @export
scale_fill_shabviz_c <- function(cmap = "viridis", ...) {
  fn <- .cmap_function(cmap)
  ggplot2::scale_fill_gradientn(colours = fn(256), ...)
}
```

- [ ] **Step 5: Run all R tests**

```bash
cd /Users/shabnamhakimi/repos/shabviz-style/r
Rscript -e "testthat::test_dir('tests/testthat', reporter = 'progress')"
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add r/R/theme.R r/R/scales.R r/tests/testthat/test-theme.R
git commit -m "feat(r): add theme parameter to theme_shabviz, setup, and discrete scales"
```

---

## Self-Review

**Spec coverage:**
- ✅ `theme="light"/"dark"/"black"` on Python `setup()`, `apply_style()`, `palette()`, `binary_palette()` — Task 2
- ✅ `theme=` on R `setup()`, `theme_shabviz()`, `palette_sv()`, `binary_palette()` — Tasks 3–4
- ✅ Per-theme color tables — Task 1 (Python), Task 4 (R)
- ✅ `_RANGE_LIGHT` / `_RANGE_DARK` (Python), `.range_light` / `.range_dark` (R) — Tasks 1, 3
- ✅ `"dark"` and `"black"` share range table — enforced in `_resolve_range` / `.resolve_range`
- ✅ `legend.frameon = True` for all themes — Task 2 `_build_rcparams`; R `legend.background` rect in Task 4
- ✅ `text.color`, `axes.titlecolor` added to Python rcParams — Task 2
- ✅ `ValueError` / `stop()` on invalid theme — Tasks 1, 2, 3, 4
- ✅ Default `theme="light"` everywhere — all tasks
- ✅ R scales pass `theme` through to `palette_sv` — Task 4

**Placeholder scan:** None found.

**Type consistency:**
- `_resolve_range(cmap, lo, hi, theme)` defined Task 1, consumed Task 2 ✅
- `_THEME_COLORS` defined Task 1, consumed Task 2 ✅
- `.resolve_range(cmap, lo, hi, theme)` defined Task 3, consumed Task 4 ✅
- `.theme_colors` defined Task 4, consumed within Task 4 ✅
- `palette_sv(..., theme)` defined Task 3, called with `theme=` in Task 4 scales ✅
