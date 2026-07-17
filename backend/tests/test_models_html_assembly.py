import pytest
from pydantic import ValidationError

from backend.models.color_style import ColorStyleResult
from backend.models.html_assembly import HtmlAssemblyRequest
from backend.models.layout import BlockType, BoundingBox, LayoutBlock, LayoutExtractionResult


def make_layout() -> LayoutExtractionResult:
    return LayoutExtractionResult(
        blocks=[
            LayoutBlock(
                type=BlockType.HEADER,
                box=BoundingBox(ymin=0, xmin=0, ymax=100, xmax=1000),
                text="Welcome",
            )
        ],
        model="gemini-test",
    )


def make_styles() -> ColorStyleResult:
    return ColorStyleResult(
        bg_color="#FFFFFF",
        heading_color="#000000",
        link_color="#0000FF",
        heading_font="sans-serif bold",
        body_font="sans-serif regular",
        body_font_size="14px",
        source="gemini",
    )


def test_accepts_http_and_https_asset_urls():
    request = HtmlAssemblyRequest(
        layout=make_layout(),
        styles=make_styles(),
        assets={0: "https://example.com/img.png", 1: "http://example.com/img2.png"},
    )
    assert request.assets[0] == "https://example.com/img.png"


def test_assets_none_by_default():
    request = HtmlAssemblyRequest(layout=make_layout(), styles=make_styles())
    assert request.assets is None


def test_rejects_javascript_scheme():
    with pytest.raises(ValidationError):
        HtmlAssemblyRequest(
            layout=make_layout(),
            styles=make_styles(),
            assets={0: "javascript:alert(1)"},
        )


def test_rejects_data_scheme():
    with pytest.raises(ValidationError):
        HtmlAssemblyRequest(
            layout=make_layout(),
            styles=make_styles(),
            assets={0: "data:text/html,<script>alert(1)</script>"},
        )


def test_accepts_data_image_png_uri():
    request = HtmlAssemblyRequest(
        layout=make_layout(),
        styles=make_styles(),
        assets={0: "data:image/png;base64,aGVsbG8="},
    )
    assert request.assets[0].startswith("data:image/png;base64,")


def test_accepts_data_image_jpeg_uri():
    request = HtmlAssemblyRequest(
        layout=make_layout(),
        styles=make_styles(),
        assets={0: "data:image/jpeg;base64,aGVsbG8="},
    )
    assert request.assets[0].startswith("data:image/jpeg;base64,")


def test_rejects_data_image_svg_uri():
    with pytest.raises(ValidationError):
        HtmlAssemblyRequest(
            layout=make_layout(),
            styles=make_styles(),
            assets={0: "data:image/svg+xml;base64,PHN2Zz48L3N2Zz4="},
        )
