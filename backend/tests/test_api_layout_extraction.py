from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app import app
from backend.config import Settings, get_settings
from backend.models.layout import BlockType, BoundingBox, LayoutBlock, LayoutExtractionResult
from backend.services.layout_extraction import LayoutExtractionError

client = TestClient(app)


def override_settings(**overrides) -> Settings:
    defaults = {"google_api_key": "test-key", "max_upload_bytes": 1024}
    defaults.update(overrides)
    return Settings(**defaults)


def teardown_function():
    app.dependency_overrides.clear()


def test_layout_extraction_success():
    app.dependency_overrides[get_settings] = lambda: override_settings()

    fake_result = LayoutExtractionResult(
        blocks=[
            LayoutBlock(
                type=BlockType.HEADER,
                box=BoundingBox(ymin=0, xmin=0, ymax=100, xmax=1000),
                text="Welcome",
            )
        ],
        degraded=False,
        model="gemini-test",
    )

    with patch(
        "backend.api.layout_extraction.extract_layout", return_value=fake_result
    ) as mock_extract:
        response = client.post(
            "/api/layout-extraction",
            files={"image": ("preview.png", b"fake-bytes", "image/png")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["degraded"] is False
    assert body["blocks"][0]["type"] == "header"
    mock_extract.assert_called_once()


def test_layout_extraction_rejects_non_image():
    app.dependency_overrides[get_settings] = lambda: override_settings()

    response = client.post(
        "/api/layout-extraction",
        files={"image": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400


def test_layout_extraction_rejects_oversized_upload():
    app.dependency_overrides[get_settings] = lambda: override_settings(max_upload_bytes=4)

    response = client.post(
        "/api/layout-extraction",
        files={"image": ("preview.png", b"fake-bytes", "image/png")},
    )

    assert response.status_code == 413


def test_layout_extraction_service_failure_returns_502():
    app.dependency_overrides[get_settings] = lambda: override_settings()

    with patch(
        "backend.api.layout_extraction.extract_layout",
        side_effect=LayoutExtractionError("boom"),
    ):
        response = client.post(
            "/api/layout-extraction",
            files={"image": ("preview.png", b"fake-bytes", "image/png")},
        )

    assert response.status_code == 502
