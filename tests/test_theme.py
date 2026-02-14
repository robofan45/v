"""Tests for theme constants, score_color boundaries, and stylesheet."""

import re

from resumeflow import theme
from resumeflow.theme import (
    APP_STYLESHEET,
    FADE_DURATION_MS,
    POPUP_WIDTH,
    SCORE_GOOD,
    SCORE_WARN,
    score_color,
)

_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

# All named palette colours exported from the module.
_PALETTE_NAMES = [
    "BASE", "MANTLE", "CRUST",
    "SURFACE0", "SURFACE1", "SURFACE2",
    "OVERLAY0", "OVERLAY1",
    "TEXT", "SUBTEXT0", "SUBTEXT1",
    "BLUE", "LAVENDER", "SKY", "TEAL", "GREEN",
    "YELLOW", "PEACH", "RED", "MAUVE", "PINK", "ROSEWATER",
]


class TestPaletteHexValues:
    """Every palette constant must be a valid 7-char hex colour."""

    def test_all_palette_colours_are_valid_hex(self):
        for name in _PALETTE_NAMES:
            value = getattr(theme, name)
            assert _HEX_RE.match(value), f"{name} = {value!r} is not valid hex"

    def test_palette_has_expected_count(self):
        assert len(_PALETTE_NAMES) == 22


class TestScoreColor:
    def test_score_100_is_green(self):
        assert score_color(100) == theme.GREEN

    def test_score_at_good_boundary(self):
        assert score_color(SCORE_GOOD) == theme.GREEN

    def test_score_just_below_good(self):
        assert score_color(SCORE_GOOD - 1) == theme.YELLOW

    def test_score_at_warn_boundary(self):
        assert score_color(SCORE_WARN) == theme.YELLOW

    def test_score_just_below_warn(self):
        assert score_color(SCORE_WARN - 1) == theme.RED

    def test_score_zero(self):
        assert score_color(0) == theme.RED

    def test_score_negative(self):
        assert score_color(-10) == theme.RED

    def test_score_very_high(self):
        assert score_color(999) == theme.GREEN


class TestStylesheetAndConstants:
    def test_stylesheet_is_non_empty(self):
        assert len(APP_STYLESHEET) > 100

    def test_stylesheet_contains_base_colour(self):
        assert theme.BASE in APP_STYLESHEET

    def test_popup_width_positive(self):
        assert POPUP_WIDTH > 0

    def test_fade_duration_positive(self):
        assert FADE_DURATION_MS > 0

    def test_score_good_greater_than_warn(self):
        assert SCORE_GOOD > SCORE_WARN > 0
