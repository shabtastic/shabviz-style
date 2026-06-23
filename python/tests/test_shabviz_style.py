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
