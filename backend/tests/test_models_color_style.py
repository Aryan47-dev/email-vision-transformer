import pytest
from pydantic import ValidationError

from backend.models.color_style import ColorStyleFields, ColorStyleResult


def make_fields(**overrides) -> dict:
    defaults = dict(
        bg_color="#FFFFFF",
        heading_color="#000000",
        link_color="#0000FF",
        heading_font="sans-serif bold",
        body_font="sans-serif regular",
        body_font_size="14px",
    )
    defaults.update(overrides)
    return defaults


def test_accepts_three_digit_hex():
    fields = ColorStyleFields(**make_fields(bg_color="#fff"))
    assert fields.bg_color == "#fff"


def test_accepts_six_digit_hex():
    fields = ColorStyleFields(**make_fields(bg_color="#ffffff"))
    assert fields.bg_color == "#ffffff"


def test_rejects_color_name():
    with pytest.raises(ValidationError):
        ColorStyleFields(**make_fields(bg_color="blue"))


def test_rejects_invalid_hex_digits():
    with pytest.raises(ValidationError):
        ColorStyleFields(**make_fields(bg_color="#gggggg"))


def test_rejects_missing_hash():
    with pytest.raises(ValidationError):
        ColorStyleFields(**make_fields(bg_color="ffffff"))


def test_color_style_result_defaults():
    result = ColorStyleResult(**make_fields(), source="gemini")
    assert result.degraded is False
    assert result.source == "gemini"


def test_color_style_result_requires_source():
    with pytest.raises(ValidationError):
        ColorStyleResult(**make_fields())
