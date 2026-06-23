"""
shabviz_style — a matplotlib/seaborn style spec for scientific figures.

Built around viridis-family colormaps and the Inter font by default, but
both are configurable, and the architecture is designed to grow as you
add presets.

Quick start
-----------
    import shabviz_style as pf
    pf.setup()                                  # default: viridis + Inter
    pf.setup(cmap='mako', font='IBM Plex Sans') # different palette and font
    pf.setup(rc_overrides={                     # one-off rcParam tweaks
        'figure.figsize': (8, 5),
        'axes.grid': True,
    })

    # Continuous: cmap is the default for image.cmap
    plt.imshow(arr)

    # Categorical: the cycle's first two slots are always the binary pair,
    # so 2-group plots get max contrast without specifying a palette.
    sns.lineplot(data=df, x='t', y='y', hue='condition')

    # When you know N up front:
    pf.palette(3)                               # unordered categorical
    pf.palette(3, ordered=True)                 # ordinal: low/medium/high
    pf.binary_palette()                         # the high-contrast pair
    pf.palette(4, cmap='mako')                  # use a viridis cousin

Cousin colormaps
----------------
    Sequential: viridis, mako, rocket, crest, flare, cividis
    Diverging:  vlag, icefire, coolwarm

The seaborn-provided cousins (mako, rocket, crest, flare, vlag, icefire)
register automatically when this module is imported (if seaborn is
installed). Without seaborn you still get the matplotlib-native maps:
viridis, cividis, coolwarm, plus plasma/inferno/magma.

Adding a new auto-installable font
----------------------------------
Append to ``_FONT_SOURCES``::

    _FONT_SOURCES['MyFont'] = [
        'https://primary.example.com/MyFont.ttf',
        'https://fallback.example.com/MyFont.ttf',
    ]

Then ``pf.setup(font='MyFont')`` will install it on demand.

Tuning the binary range for darker cousins
------------------------------------------
``mako`` and ``rocket`` have very dark low ends. The module lifts the
default ``lo`` to 0.20 for those. Override per-call with ``lo=`` and
``hi=`` on ``palette()`` / ``binary_palette()``.
"""

from __future__ import annotations

from pathlib import Path
import urllib.request

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager
from cycler import cycler

# Importing seaborn (if available) registers the viridis cousin colormaps
# (mako, rocket, crest, flare, vlag, icefire) into matplotlib's colormap registry.
try:
    import seaborn as _sns  # noqa: F401
    _HAS_SEABORN = True
except ImportError:
    _HAS_SEABORN = False


__all__ = [
    'setup', 'apply_style', 'install_font',
    'palette', 'binary_palette',
    'SEQUENTIAL_CMAPS', 'DIVERGING_CMAPS',
    '_THEME_COLORS', '_RANGE_LIGHT', '_RANGE_DARK', '_resolve_range',
]


SEQUENTIAL_CMAPS = ['viridis', 'mako', 'rocket', 'crest', 'flare', 'cividis']
DIVERGING_CMAPS = ['vlag', 'icefire', 'coolwarm']


# ---------------------------------------------------------------------------
# Font registry
# ---------------------------------------------------------------------------
# Each entry maps a font family name to a list of fallback URLs (tried in
# order). Variable fonts are preferred — one file covers all weights.
# Add new fonts here to make them auto-installable.

_FONT_SOURCES = {
    'Inter': [
        'https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf',
        'https://github.com/google/fonts/raw/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf',
        'https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf',
    ],
    'Source Sans 3': [
        'https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/sourcesans3/SourceSans3%5Bwght%5D.ttf',
        'https://github.com/google/fonts/raw/main/ofl/sourcesans3/SourceSans3%5Bwght%5D.ttf',
        'https://raw.githubusercontent.com/google/fonts/main/ofl/sourcesans3/SourceSans3%5Bwght%5D.ttf',
    ],
    'IBM Plex Sans': [
        'https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/ibmplexsans/IBMPlexSans-Regular.ttf',
        'https://github.com/google/fonts/raw/main/ofl/ibmplexsans/IBMPlexSans-Regular.ttf',
        'https://raw.githubusercontent.com/google/fonts/main/ofl/ibmplexsans/IBMPlexSans-Regular.ttf',
    ],
}


def install_font(name: str = 'Inter', force: bool = False) -> bool:
    """Download a registered font into matplotlib's cache and register it.

    Returns True if the font is available after this call, else False.
    Safe to call repeatedly — it's a no-op if already registered.

    For fonts not in ``_FONT_SOURCES``, returns whether the font is already
    available system-wide (no download attempted).
    """
    available = {f.name for f in font_manager.fontManager.ttflist}
    if name in available and not force:
        return True

    if name not in _FONT_SOURCES:
        return name in available

    cache = Path(mpl.get_cachedir()) / 'shabviz_style_fonts'
    cache.mkdir(exist_ok=True)
    target = cache / f'{name.replace(" ", "_")}.ttf'

    if not target.exists() or force:
        last_err = None
        for url in _FONT_SOURCES[name]:
            try:
                urllib.request.urlretrieve(url, target)
                last_err = None
                break
            except Exception as e:
                last_err = e
        if last_err is not None:
            print(f'[shabviz_style] Could not download {name}: {last_err}')
            return False

    try:
        font_manager.fontManager.addfont(str(target))
    except Exception as e:
        print(f'[shabviz_style] Could not register {name}: {e}')
        return False

    return name in {f.name for f in font_manager.fontManager.ttflist}


# ---------------------------------------------------------------------------
# Palette helpers
# ---------------------------------------------------------------------------

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


def _resolve_range(cmap: str, lo, hi, theme: str = 'light'):
    if theme not in _VALID_THEMES:
        raise ValueError(f"theme must be one of {sorted(_VALID_THEMES)!r}, got {theme!r}")
    range_table = _RANGE_LIGHT if theme == 'light' else _RANGE_DARK
    fallback = _FALLBACK_RANGE if theme == 'light' else _FALLBACK_RANGE_DARK
    default_lo, default_hi = range_table.get(cmap, fallback)
    return (default_lo if lo is None else lo,
            default_hi if hi is None else hi)


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
    if theme not in _VALID_THEMES:
        raise ValueError(f"theme must be one of {sorted(_VALID_THEMES)!r}, got {theme!r}")
    cm = mpl.colormaps[cmap]
    if positions is None:
        positions = _resolve_range(cmap, None, None, theme)
    return [cm(positions[0]), cm(positions[1])]


def _maxdist_reorder(items):
    """Reorder so the result starts with both endpoints (max contrast for
    binary use), then fills in by greedy max-min-distance."""
    n = len(items)
    if n <= 2:
        return list(items)
    out = [0, n - 1]
    while len(out) < n:
        candidates = [i for i in range(n) if i not in out]
        i = max(candidates, key=lambda c: min(abs(c - o) for o in out))
        out.append(i)
    return [items[i] for i in out]


# ---------------------------------------------------------------------------
# rcParams
# ---------------------------------------------------------------------------

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


def apply_style(cmap: str = 'viridis', font: str = 'Inter',
                theme: str = 'light', rc_overrides: dict = None):
    """Apply rcParams without touching font installation."""
    rc = _build_rcparams(cmap=cmap, font=font, theme=theme)
    if rc_overrides:
        rc.update(rc_overrides)
    plt.rcParams.update(rc)


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
    if theme not in _VALID_THEMES:
        raise ValueError(f"theme must be one of {sorted(_VALID_THEMES)!r}, got {theme!r}")
    if auto_install:
        ok = install_font(font)
        if verbose:
            msg = (f'{font} registered.' if ok
                   else f'{font} not available; using fallback sans-serif.')
            print(f'[shabviz_style] {msg}')

    apply_style(cmap=cmap, font=font, theme=theme, rc_overrides=rc_overrides)
    if verbose:
        print(f'[shabviz_style] Style applied (cmap={cmap}, font={font}, theme={theme}).')
