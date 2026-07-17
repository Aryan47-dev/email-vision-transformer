import io
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from backend.config import Settings
from backend.services.layout_extraction import (
    LayoutExtractionError,
    _downscale_if_needed,
    extract_layout,
)


def make_settings(**overrides) -> Settings:
    defaults = {"google_api_key": "test-key", "gemini_model": "gemini-test"}
    defaults.update(overrides)
    return Settings(**defaults)


def make_response(parsed=None, text=None) -> MagicMock:
    response = MagicMock()
    response.parsed = parsed
    response.text = text
    response.candidates = []
    return response


def make_image_bytes(width, height, fmt="PNG") -> bytes:
    img = Image.new("RGB", (width, height), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


@patch("backend.services.layout_extraction.genai.Client")
def test_extract_layout_happy_path(mock_client_cls):
    valid_blocks = [
        {
            "type": "header",
            "box": {"ymin": 0, "xmin": 0, "ymax": 100, "xmax": 1000},
            "text": "Welcome",
        }
    ]
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = make_response(parsed=valid_blocks)
    mock_client_cls.return_value = mock_client

    result = extract_layout(b"fake-image-bytes", "image/png", make_settings())

    assert result.degraded is False
    assert len(result.blocks) == 1
    assert result.blocks[0].type == "header"
    assert result.blocks[0].text == "Welcome"
    mock_client.models.generate_content.assert_called_once()


@patch("backend.services.layout_extraction.genai.Client")
def test_extract_layout_passes_max_output_tokens(mock_client_cls):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = make_response(
        parsed=[{"type": "header", "box": {"ymin": 0, "xmin": 0, "ymax": 100, "xmax": 1000}}]
    )
    mock_client_cls.return_value = mock_client

    extract_layout(b"fake-image-bytes", "image/png", make_settings())

    config = mock_client.models.generate_content.call_args.kwargs["config"]
    assert config.max_output_tokens == 8192


@patch("backend.services.layout_extraction.genai.Client")
def test_extract_layout_falls_back_on_empty_response(mock_client_cls):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = make_response(parsed=None, text="")
    mock_client_cls.return_value = mock_client

    result = extract_layout(b"fake-image-bytes", "image/png", make_settings())

    assert result.degraded is True
    assert len(result.blocks) == 1
    # fallback now renders as an image block (referencing the caller's own
    # upload, injected by the orchestration layer) rather than blank text
    assert result.blocks[0].type == "image"
    # one initial attempt + one retry
    assert mock_client.models.generate_content.call_count == 2


@patch("backend.services.layout_extraction.genai.Client")
def test_extract_layout_falls_back_on_sdk_exception(mock_client_cls):
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = RuntimeError("API error")
    mock_client_cls.return_value = mock_client

    result = extract_layout(b"fake-image-bytes", "image/png", make_settings())

    assert result.degraded is True
    assert len(result.blocks) == 1
    assert result.blocks[0].type == "image"


def test_extract_layout_raises_without_api_key():
    with pytest.raises(LayoutExtractionError):
        extract_layout(b"fake-image-bytes", "image/png", make_settings(google_api_key=""))


def test_downscale_leaves_small_image_unchanged():
    small_bytes = make_image_bytes(200, 200)

    result_bytes, result_mime = _downscale_if_needed(small_bytes, "image/png")

    assert result_bytes == small_bytes
    assert result_mime == "image/png"


def test_downscale_shrinks_oversized_tall_image():
    tall_bytes = make_image_bytes(600, 5141)

    result_bytes, result_mime = _downscale_if_needed(tall_bytes, "image/png")

    assert result_mime == "image/png"
    with Image.open(io.BytesIO(result_bytes)) as resized:
        assert max(resized.size) <= 2048


def test_downscale_returns_original_on_invalid_image():
    result_bytes, result_mime = _downscale_if_needed(b"not-an-image", "image/png")

    assert result_bytes == b"not-an-image"
    assert result_mime == "image/png"
