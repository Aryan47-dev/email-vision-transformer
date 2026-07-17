from unittest.mock import MagicMock, patch

import pytest

from backend.config import Settings
from backend.services.ocr_extraction import OcrExtractionError, extract_text


def make_settings(**overrides) -> Settings:
    defaults = {"google_api_key": "test-key"}
    defaults.update(overrides)
    return Settings(**defaults)


def make_response(parsed=None, text=None) -> MagicMock:
    response = MagicMock()
    response.parsed = parsed
    response.text = text
    return response


VALID_BLOCKS = [
    {"text": "Welcome", "box": {"ymin": 0, "xmin": 0, "ymax": 100, "xmax": 500}},
    {"text": "Shop Now", "box": {"ymin": 200, "xmin": 0, "ymax": 300, "xmax": 400}},
]


@patch("backend.services.ocr_extraction.genai.Client")
def test_extract_text_happy_path(mock_client_cls):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = make_response(parsed=VALID_BLOCKS)
    mock_client_cls.return_value = mock_client

    result = extract_text(b"fake-image-bytes", "image/png", make_settings())

    assert result.full_text == "Welcome\nShop Now"
    assert len(result.blocks) == 2
    assert result.blocks[0].text == "Welcome"
    mock_client.models.generate_content.assert_called_once()


@patch("backend.services.ocr_extraction.genai.Client")
def test_extract_text_empty_result_is_valid_no_retry(mock_client_cls):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = make_response(parsed=[])
    mock_client_cls.return_value = mock_client

    result = extract_text(b"fake-image-bytes", "image/png", make_settings())

    assert result.full_text == ""
    assert result.blocks == []
    # a valid empty array should not trigger a retry
    mock_client.models.generate_content.assert_called_once()


@patch("backend.services.ocr_extraction.genai.Client")
def test_extract_text_falls_back_on_unparseable_response(mock_client_cls):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = make_response(parsed=None, text="")
    mock_client_cls.return_value = mock_client

    result = extract_text(b"fake-image-bytes", "image/png", make_settings())

    assert result.full_text == ""
    assert result.blocks == []
    # one initial attempt + one retry
    assert mock_client.models.generate_content.call_count == 2


@patch("backend.services.ocr_extraction.genai.Client")
def test_extract_text_falls_back_on_sdk_exception(mock_client_cls):
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = RuntimeError("API error")
    mock_client_cls.return_value = mock_client

    result = extract_text(b"fake-image-bytes", "image/png", make_settings())

    assert result.full_text == ""
    assert result.blocks == []


def test_extract_text_raises_without_api_key():
    with pytest.raises(OcrExtractionError):
        extract_text(b"fake-image-bytes", "image/png", make_settings(google_api_key=""))
