from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app import app
from backend.config import Settings, get_settings
from backend.models.color_style import ColorStyleResult
from backend.services.color_style import ColorStyleExtractionError

client = TestClient(app)


def override_settings(**overrides) -> Settings:
    defaults = {
        "google_api_key": "gemini-key",
        "google_cloud_vision_api_key": "vision-key",
        "max_upload_bytes": 1024,
    }
    defaults.update(overrides)
    return Settings(**defaults)


def teardown_function():
    app.dependency_overrides.clear()


def test_color_style_success():
    app.dependency_overrides[get_settings] = lambda: override_settings()

    fake_result = ColorStyleResult(
        bg_color="#FFFFFF",
        heading_color="#000000",
        link_color="#0000FF",
        heading_font="sans-serif bold",
        body_font="sans-serif regular",
        body_font_size="14px",
        degraded=False,
        source="gemini",
    )

    with patch(
        "backend.api.color_style.extract_color_style", return_value=fake_result
    ) as mock_extract:
        response = client.post(
            "/api/color-style",
            files={"image": ("preview.png", b"fake-bytes", "image/png")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "gemini"
    assert body["bg_color"] == "#FFFFFF"
    mock_extract.assert_called_once()


def test_color_style_rejects_non_image():
    app.dependency_overrides[get_settings] = lambda: override_settings()

    response = client.post(
        "/api/color-style",
        files={"image": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400


def test_color_style_rejects_oversized_upload():
    app.dependency_overrides[get_settings] = lambda: override_settings(max_upload_bytes=4)

    response = client.post(
        "/api/color-style",
        files={"image": ("preview.png", b"fake-bytes", "image/png")},
    )

    assert response.status_code == 413


def test_color_style_service_failure_returns_502():
    app.dependency_overrides[get_settings] = lambda: override_settings()

    with patch(
        "backend.api.color_style.extract_color_style",
        side_effect=ColorStyleExtractionError("boom"),
    ):
        response = client.post(
            "/api/color-style",
            files={"image": ("preview.png", b"fake-bytes", "image/png")},
        )

    assert response.status_code == 502
