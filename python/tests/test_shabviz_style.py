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


def test_binary_palette_default_returns_two_colors():
    pair = pf.binary_palette()
    assert len(pair) == 2


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
