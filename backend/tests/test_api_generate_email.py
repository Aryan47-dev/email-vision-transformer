from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from backend.app import app
from backend.config import Settings, get_settings
from backend.models.generate_email import GenerateEmailResult
from backend.services.generate_email import GenerateEmailError

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


def test_generate_email_success_no_assets():
    app.dependency_overrides[get_settings] = lambda: override_settings()

    fake_result = GenerateEmailResult(html="<html>hi</html>")

    with patch(
        "backend.api.generate_email.generate_email",
        new=AsyncMock(return_value=fake_result),
    ) as mock_generate:
        response = client.post(
            "/api/generate-email",
            files={"image": ("preview.png", b"fake-bytes", "image/png")},
        )

    assert response.status_code == 200
    assert response.json()["html"] == "<html>hi</html>"
    mock_generate.assert_called_once()
    assert mock_generate.call_args.args[2] is None


def test_generate_email_success_with_assets():
    app.dependency_overrides[get_settings] = lambda: override_settings()

    fake_result = GenerateEmailResult(html="<html>hi</html>")

    with patch(
        "backend.api.generate_email.generate_email",
        new=AsyncMock(return_value=fake_result),
    ) as mock_generate:
        response = client.post(
            "/api/generate-email",
            files={"image": ("preview.png", b"fake-bytes", "image/png")},
            data={"assets": '["https://example.com/a.png"]'},
        )

    assert response.status_code == 200
    assert mock_generate.call_args.args[2] == ["https://example.com/a.png"]


def test_generate_email_rejects_malformed_assets_json():
    app.dependency_overrides[get_settings] = lambda: override_settings()

    response = client.post(
        "/api/generate-email",
        files={"image": ("preview.png", b"fake-bytes", "image/png")},
        data={"assets": "not-json"},
    )

    assert response.status_code == 400


def test_generate_email_rejects_non_image():
    app.dependency_overrides[get_settings] = lambda: override_settings()

    response = client.post(
        "/api/generate-email",
        files={"image": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400


def test_generate_email_rejects_oversized_upload():
    app.dependency_overrides[get_settings] = lambda: override_settings(max_upload_bytes=4)

    response = client.post(
        "/api/generate-email",
        files={"image": ("preview.png", b"fake-bytes", "image/png")},
    )

    assert response.status_code == 413


def test_generate_email_service_failure_returns_502():
    app.dependency_overrides[get_settings] = lambda: override_settings()

    with patch(
        "backend.api.generate_email.generate_email",
        new=AsyncMock(side_effect=GenerateEmailError("boom")),
    ):
        response = client.post(
            "/api/generate-email",
            files={"image": ("preview.png", b"fake-bytes", "image/png")},
        )

    assert response.status_code == 502
