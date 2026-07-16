from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app)


def make_payload(**overrides) -> dict:
    payload = {
        "layout": {
            "blocks": [
                {
                    "type": "header",
                    "box": {"ymin": 0, "xmin": 0, "ymax": 100, "xmax": 1000},
                    "text": "Welcome",
                }
            ],
            "degraded": False,
            "model": "gemini-test",
        },
        "styles": {
            "bg_color": "#FFFFFF",
            "heading_color": "#000000",
            "link_color": "#0000FF",
            "heading_font": "sans-serif bold",
            "body_font": "sans-serif regular",
            "body_font_size": "14px",
            "degraded": False,
            "source": "gemini",
        },
    }
    payload.update(overrides)
    return payload


def test_html_assembly_success():
    response = client.post("/api/html-assembly", json=make_payload())

    assert response.status_code == 200
    body = response.json()
    assert "Welcome" in body["html"]
    assert "<table" in body["html"]


def test_html_assembly_rejects_invalid_asset_url_scheme():
    response = client.post(
        "/api/html-assembly",
        json=make_payload(assets={"0": "javascript:alert(1)"}),
    )

    assert response.status_code == 422


def test_html_assembly_empty_blocks_still_succeeds():
    payload = make_payload()
    payload["layout"]["blocks"] = []

    response = client.post("/api/html-assembly", json=payload)

    assert response.status_code == 200
    assert "<table" in response.json()["html"]
