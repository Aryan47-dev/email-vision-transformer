from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from backend.config import Settings
from backend.services.color_style import ColorStyleExtractionError, extract_color_style


def make_settings(**overrides) -> Settings:
    defaults = {
        "google_api_key": "gemini-key",
        "google_cloud_vision_api_key": "vision-key",
    }
    defaults.update(overrides)
    return Settings(**defaults)


def make_gemini_response(parsed=None, text=None):
    return SimpleNamespace(parsed=parsed, text=text)


def make_color(r, g, b, pixel_fraction):
    return SimpleNamespace(
        color=SimpleNamespace(red=r, green=g, blue=b),
        pixel_fraction=pixel_fraction,
    )


def make_vision_response(colors, error_message=""):
    return SimpleNamespace(
        image_properties_annotation=SimpleNamespace(
            dominant_colors=SimpleNamespace(colors=colors)
        ),
        error=SimpleNamespace(message=error_message),
    )


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
    mock_client.models.generate_content.return_value = make_gemini_response(
        parsed=VALID_GEMINI_FIELDS
    )
    mock_client_cls.return_value = mock_client

    result = extract_color_style(b"fake-bytes", "image/png", make_settings())

    assert result.source == "gemini"
    assert result.degraded is False
    assert result.bg_color == "#FFFFFF"
    mock_client.models.generate_content.assert_called_once()


@patch("backend.services.color_style.vision.ImageAnnotatorClient")
@patch("backend.services.color_style.genai.Client")
def test_gemini_invalid_hex_falls_back_to_vision(mock_gemini_cls, mock_vision_cls):
    mock_gemini_client = MagicMock()
    mock_gemini_client.models.generate_content.return_value = make_gemini_response(
        parsed={**VALID_GEMINI_FIELDS, "bg_color": "blue"}
    )
    mock_gemini_cls.return_value = mock_gemini_client

    mock_vision_client = MagicMock()
    mock_vision_client.image_properties.return_value = make_vision_response(
        [make_color(255, 255, 255, 0.5), make_color(0, 0, 0, 0.3), make_color(0, 0, 255, 0.2)]
    )
    mock_vision_cls.return_value = mock_vision_client

    result = extract_color_style(b"fake-bytes", "image/png", make_settings())

    assert result.source == "vision_fallback"
    assert result.degraded is True
    # both gemini attempts (initial + retry) should have been tried
    assert mock_gemini_client.models.generate_content.call_count == 2


@patch("backend.services.color_style.vision.ImageAnnotatorClient")
@patch("backend.services.color_style.genai.Client")
def test_gemini_sdk_exception_falls_back_to_vision(mock_gemini_cls, mock_vision_cls):
    mock_gemini_client = MagicMock()
    mock_gemini_client.models.generate_content.side_effect = RuntimeError("boom")
    mock_gemini_cls.return_value = mock_gemini_client

    mock_vision_client = MagicMock()
    mock_vision_client.image_properties.return_value = make_vision_response(
        [make_color(255, 255, 255, 0.5), make_color(0, 0, 0, 0.3), make_color(0, 0, 255, 0.2)]
    )
    mock_vision_cls.return_value = mock_vision_client

    result = extract_color_style(b"fake-bytes", "image/png", make_settings())

    assert result.source == "vision_fallback"


@patch("backend.services.color_style.vision.ImageAnnotatorClient")
def test_vision_fallback_rank_maps_colors(mock_vision_cls):
    mock_vision_client = MagicMock()
    # deliberately out of order - service must sort by pixel_fraction descending
    mock_vision_client.image_properties.return_value = make_vision_response(
        [
            make_color(0, 0, 255, 0.1),  # least dominant -> link
            make_color(255, 255, 255, 0.6),  # most dominant -> bg
            make_color(0, 0, 0, 0.3),  # 2nd most dominant -> heading
        ]
    )
    mock_vision_cls.return_value = mock_vision_client

    result = extract_color_style(
        b"fake-bytes", "image/png", make_settings(google_api_key="")
    )

    assert result.source == "vision_fallback"
    assert result.bg_color == "#FFFFFF"
    assert result.heading_color == "#000000"
    assert result.link_color == "#0000FF"


@patch("backend.services.color_style.vision.ImageAnnotatorClient")
def test_vision_fallback_pads_when_fewer_than_three_colors(mock_vision_cls):
    mock_vision_client = MagicMock()
    mock_vision_client.image_properties.return_value = make_vision_response(
        [make_color(255, 0, 0, 1.0)]
    )
    mock_vision_cls.return_value = mock_vision_client

    result = extract_color_style(
        b"fake-bytes", "image/png", make_settings(google_api_key="")
    )

    assert result.bg_color == "#FF0000"
    assert result.heading_color == "#000000"
    assert result.link_color == "#000000"


def test_skips_gemini_when_api_key_missing():
    with patch("backend.services.color_style.vision.ImageAnnotatorClient") as mock_vision_cls:
        mock_vision_client = MagicMock()
        mock_vision_client.image_properties.return_value = make_vision_response([])
        mock_vision_cls.return_value = mock_vision_client

        with patch("backend.services.color_style.genai.Client") as mock_gemini_cls:
            result = extract_color_style(
                b"fake-bytes", "image/png", make_settings(google_api_key="")
            )
            mock_gemini_cls.assert_not_called()

    assert result.source == "vision_fallback"


def test_raises_when_both_gemini_and_vision_fail():
    with patch("backend.services.color_style.genai.Client") as mock_gemini_cls:
        mock_gemini_client = MagicMock()
        mock_gemini_client.models.generate_content.side_effect = RuntimeError("boom")
        mock_gemini_cls.return_value = mock_gemini_client

        with pytest.raises(ColorStyleExtractionError):
            extract_color_style(
                b"fake-bytes",
                "image/png",
                make_settings(google_cloud_vision_api_key=""),
            )
