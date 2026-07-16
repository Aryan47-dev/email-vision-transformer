from unittest.mock import MagicMock, patch

import pytest

from backend.config import Settings
from backend.services.layout_extraction import LayoutExtractionError, extract_layout


def make_settings(**overrides) -> Settings:
    defaults = {"google_api_key": "test-key", "gemini_model": "gemini-test"}
    defaults.update(overrides)
    return Settings(**defaults)


def make_response(parsed=None, text=None) -> MagicMock:
    response = MagicMock()
    response.parsed = parsed
    response.text = text
    return response


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
def test_extract_layout_falls_back_on_empty_response(mock_client_cls):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = make_response(parsed=None, text="")
    mock_client_cls.return_value = mock_client

    result = extract_layout(b"fake-image-bytes", "image/png", make_settings())

    assert result.degraded is True
    assert len(result.blocks) == 1
    assert result.blocks[0].type == "other"
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


def test_extract_layout_raises_without_api_key():
    with pytest.raises(LayoutExtractionError):
        extract_layout(b"fake-image-bytes", "image/png", make_settings(google_api_key=""))
