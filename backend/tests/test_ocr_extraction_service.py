import io
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from backend.config import Settings
from backend.services.ocr_extraction import OcrExtractionError, extract_text


def make_settings(**overrides) -> Settings:
    defaults = {"google_cloud_vision_api_key": "test-key"}
    defaults.update(overrides)
    return Settings(**defaults)


def make_image_bytes(width=200, height=100) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color="white").save(buf, format="PNG")
    return buf.getvalue()


def make_annotation(description: str, vertices: list[tuple[int, int]]):
    return SimpleNamespace(
        description=description,
        bounding_poly=SimpleNamespace(
            vertices=[SimpleNamespace(x=x, y=y) for x, y in vertices]
        ),
    )


def make_response(annotations, error_message=""):
    return SimpleNamespace(
        text_annotations=annotations,
        error=SimpleNamespace(message=error_message),
    )


@patch("backend.services.ocr_extraction.vision.ImageAnnotatorClient")
def test_extract_text_happy_path(mock_client_cls):
    annotations = [
        make_annotation("Hello World", [(0, 0), (200, 0), (200, 100), (0, 100)]),
        make_annotation("Hello", [(0, 0), (100, 0), (100, 50), (0, 50)]),
        make_annotation("World", [(100, 50), (200, 50), (200, 100), (100, 100)]),
    ]
    mock_client = MagicMock()
    mock_client.text_detection.return_value = make_response(annotations)
    mock_client_cls.return_value = mock_client

    result = extract_text(make_image_bytes(200, 100), make_settings())

    assert result.full_text == "Hello World"
    assert len(result.blocks) == 2
    assert result.blocks[0].text == "Hello"
    assert result.blocks[0].box.xmin == 0
    assert result.blocks[0].box.xmax == 500
    mock_client.text_detection.assert_called_once()


@patch("backend.services.ocr_extraction.vision.ImageAnnotatorClient")
def test_extract_text_empty_result_is_not_an_error(mock_client_cls):
    mock_client = MagicMock()
    mock_client.text_detection.return_value = make_response([])
    mock_client_cls.return_value = mock_client

    result = extract_text(make_image_bytes(), make_settings())

    assert result.full_text == ""
    assert result.blocks == []


@patch("backend.services.ocr_extraction.vision.ImageAnnotatorClient")
def test_extract_text_retries_then_raises_on_api_error(mock_client_cls):
    mock_client = MagicMock()
    mock_client.text_detection.return_value = make_response([], error_message="quota exceeded")
    mock_client_cls.return_value = mock_client

    with pytest.raises(OcrExtractionError):
        extract_text(make_image_bytes(), make_settings())

    assert mock_client.text_detection.call_count == 2


@patch("backend.services.ocr_extraction.vision.ImageAnnotatorClient")
def test_extract_text_retries_then_raises_on_sdk_exception(mock_client_cls):
    mock_client = MagicMock()
    mock_client.text_detection.side_effect = RuntimeError("network error")
    mock_client_cls.return_value = mock_client

    with pytest.raises(OcrExtractionError):
        extract_text(make_image_bytes(), make_settings())

    assert mock_client.text_detection.call_count == 2


def test_extract_text_raises_without_api_key():
    with pytest.raises(OcrExtractionError):
        extract_text(make_image_bytes(), make_settings(google_cloud_vision_api_key=""))
