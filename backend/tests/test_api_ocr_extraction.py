from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app import app
from backend.config import Settings, get_settings
from backend.models.layout import BoundingBox
from backend.models.ocr import OcrBlock, OcrExtractionResult
from backend.services.ocr_extraction import OcrExtractionError

client = TestClient(app)


def override_settings(**overrides) -> Settings:
    defaults = {"google_api_key": "test-key", "max_upload_bytes": 1024}
    defaults.update(overrides)
    return Settings(**defaults)


def teardown_function():
    app.dependency_overrides.clear()


def test_ocr_extraction_success():
    app.dependency_overrides[get_settings] = lambda: override_settings()

    fake_result = OcrExtractionResult(
        full_text="Hello World",
        blocks=[
            OcrBlock(text="Hello", box=BoundingBox(ymin=0, xmin=0, ymax=100, xmax=500)),
        ],
    )

    with patch(
        "backend.api.ocr_extraction.extract_text", return_value=fake_result
    ) as mock_extract:
        response = client.post(
            "/api/ocr-extraction",
            files={"image": ("preview.png", b"fake-bytes", "image/png")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["full_text"] == "Hello World"
    assert body["blocks"][0]["text"] == "Hello"
    mock_extract.assert_called_once()


def test_ocr_extraction_rejects_non_image():
    app.dependency_overrides[get_settings] = lambda: override_settings()

    response = client.post(
        "/api/ocr-extraction",
        files={"image": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400


def test_ocr_extraction_rejects_oversized_upload():
    app.dependency_overrides[get_settings] = lambda: override_settings(max_upload_bytes=4)

    response = client.post(
        "/api/ocr-extraction",
        files={"image": ("preview.png", b"fake-bytes", "image/png")},
    )

    assert response.status_code == 413


def test_ocr_extraction_service_failure_returns_502():
    app.dependency_overrides[get_settings] = lambda: override_settings()

    with patch(
        "backend.api.ocr_extraction.extract_text",
        side_effect=OcrExtractionError("boom"),
    ):
        response = client.post(
            "/api/ocr-extraction",
            files={"image": ("preview.png", b"fake-bytes", "image/png")},
        )

    assert response.status_code == 502
