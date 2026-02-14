"""Tests for the theme module."""

from resumeflow import theme
from resumeflow.theme import score_color, SCORE_GOOD, SCORE_WARN


class TestScoreColor:
    def test_high_score_returns_green(self):
        assert score_color(100) == theme.GREEN

    def test_score_at_good_threshold(self):
        assert score_color(SCORE_GOOD) == theme.GREEN

    def test_score_just_below_good(self):
        assert score_color(SCORE_GOOD - 1) == theme.YELLOW

    def test_score_at_warn_threshold(self):
        assert score_color(SCORE_WARN) == theme.YELLOW

    def test_score_just_below_warn(self):
        assert score_color(SCORE_WARN - 1) == theme.RED

    def test_zero_score_returns_red(self):
        assert score_color(0) == theme.RED


class TestThemeConstants:
    def test_palette_colours_are_hex(self):
        for name in ("BASE", "MANTLE", "CRUST", "TEXT", "BLUE", "GREEN",
                      "YELLOW", "RED", "MAUVE"):
            value = getattr(theme, name)
            assert value.startswith("#"), f"{name} should be a hex colour"
            assert len(value) == 7, f"{name} should be #RRGGBB"

    def test_app_stylesheet_is_nonempty_string(self):
        assert isinstance(theme.APP_STYLESHEET, str)
        assert len(theme.APP_STYLESHEET) > 100

    def test_popup_width_is_positive(self):
        assert theme.POPUP_WIDTH > 0

    def test_fade_duration_is_positive(self):
        assert theme.FADE_DURATION_MS > 0
