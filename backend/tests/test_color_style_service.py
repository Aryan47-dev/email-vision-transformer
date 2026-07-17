import io
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from backend.config import Settings
from backend.services.color_style import ColorStyleExtractionError, extract_color_style


def make_settings(**overrides) -> Settings:
    defaults = {"google_api_key": "test-key"}
    defaults.update(overrides)
    return Settings(**defaults)


def make_response(parsed=None, text=None) -> MagicMock:
    response = MagicMock()
    response.parsed = parsed
    response.text = text
    return response


def make_two_color_image_bytes(dominant=(200, 30, 30), minor=(10, 10, 200)) -> bytes:
    img = Image.new("RGB", (100, 100), color=dominant)
    for x in range(50):
        for y in range(50):
            img.putpixel((x, y), minor)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_solid_image_bytes(color=(120, 200, 60)) -> bytes:
    img = Image.new("RGB", (60, 60), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


VALID_GEMINI_FIELDS = {
    "bg_color": "#FFFFFF",
    "heading_color": "#111111",
    "link_color": "#0000FF",
    "heading_font": "serif bold",
    "body_font": "serif regular",
    "body_font_size": "16px",
}


@patch("backend.services.color_style.genai.Client")
def test_gemini_happy_path(mock_client_cls):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = make_response(
        parsed=VALID_GEMINI_FIELDS
    )
    mock_client_cls.return_value = mock_client

    result = extract_color_style(make_solid_image_bytes(), "image/png", make_settings())

    assert result.source == "gemini"
    assert result.degraded is False
    assert result.bg_color == "#FFFFFF"
    mock_client.models.generate_content.assert_called_once()


@patch("backend.services.color_style.genai.Client")
def test_gemini_invalid_hex_falls_back_to_local(mock_client_cls):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = make_response(
        parsed={**VALID_GEMINI_FIELDS, "bg_color": "blue"}
    )
    mock_client_cls.return_value = mock_client

    result = extract_color_style(make_two_color_image_bytes(), "image/png", make_settings())

    assert result.source == "local_fallback"
    assert result.degraded is True
    # both gemini attempts (initial + retry) should have been tried
    assert mock_client.models.generate_content.call_count == 2


@patch("backend.services.color_style.genai.Client")
def test_gemini_sdk_exception_falls_back_to_local(mock_client_cls):
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = RuntimeError("boom")
    mock_client_cls.return_value = mock_client

    result = extract_color_style(make_two_color_image_bytes(), "image/png", make_settings())

    assert result.source == "local_fallback"


def test_local_fallback_rank_maps_dominant_colors():
    image_bytes = make_two_color_image_bytes(dominant=(200, 30, 30), minor=(10, 10, 200))

    result = extract_color_style(image_bytes, "image/png", make_settings(google_api_key=""))

    assert result.source == "local_fallback"
    assert result.bg_color == "#C81E1E"
    assert result.heading_color == "#0A0AC8"
    assert result.link_color == "#000000"


def test_local_fallback_pads_when_image_has_one_color():
    image_bytes = make_solid_image_bytes(color=(120, 200, 60))

    result = extract_color_style(image_bytes, "image/png", make_settings(google_api_key=""))

    assert result.bg_color == "#78C83C"
    assert result.heading_color == "#000000"
    assert result.link_color == "#000000"


def test_skips_gemini_when_api_key_missing():
    with patch("backend.services.color_style.genai.Client") as mock_gemini_cls:
        result = extract_color_style(
            make_solid_image_bytes(), "image/png", make_settings(google_api_key="")
        )
        mock_gemini_cls.assert_not_called()

    assert result.source == "local_fallback"


def test_raises_when_image_bytes_are_unreadable():
    with pytest.raises(ColorStyleExtractionError):
        extract_color_style(b"not-an-image", "image/png", make_settings(google_api_key=""))
