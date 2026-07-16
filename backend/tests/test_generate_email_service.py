import asyncio
from unittest.mock import patch

import pytest

from backend.config import Settings
from backend.models.color_style import ColorStyleResult
from backend.models.layout import BlockType, BoundingBox, LayoutBlock, LayoutExtractionResult
from backend.services.generate_email import (
    GenerateEmailError,
    _build_assets_map,
    generate_email,
)
from backend.services.layout_extraction import LayoutExtractionError


def make_settings() -> Settings:
    return Settings(google_api_key="key", google_cloud_vision_api_key="key")


def make_layout(*block_types: BlockType) -> LayoutExtractionResult:
    box = BoundingBox(ymin=0, xmin=0, ymax=100, xmax=1000)
    return LayoutExtractionResult(
        blocks=[LayoutBlock(type=t, box=box, text="x") for t in block_types],
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


def test_build_assets_map_matches_image_blocks_in_order():
    layout = make_layout(
        BlockType.HEADER, BlockType.IMAGE, BlockType.PARAGRAPH, BlockType.IMAGE, BlockType.IMAGE
    )
    assets = _build_assets_map(layout, ["https://a.com/1.png", "https://a.com/2.png"])

    assert assets == {1: "https://a.com/1.png", 3: "https://a.com/2.png"}
    assert 4 not in assets


def test_build_assets_map_none_when_no_urls():
    layout = make_layout(BlockType.IMAGE)
    assert _build_assets_map(layout, None) == {}


@patch("backend.services.generate_email.build_email_html", return_value="<html>ok</html>")
@patch("backend.services.generate_email.extract_color_style")
@patch("backend.services.generate_email.extract_layout")
def test_generate_email_happy_path(mock_layout, mock_styles, mock_build):
    mock_layout.return_value = make_layout(BlockType.HEADER)
    mock_styles.return_value = make_styles()

    result = asyncio.run(generate_email(b"bytes", "image/png", None, make_settings()))

    assert result.html == "<html>ok</html>"
    mock_build.assert_called_once()


@patch("backend.services.generate_email.extract_color_style")
@patch("backend.services.generate_email.extract_layout")
def test_generate_email_wraps_layout_failure(mock_layout, mock_styles):
    mock_layout.side_effect = LayoutExtractionError("boom")
    mock_styles.return_value = make_styles()

    with pytest.raises(GenerateEmailError):
        asyncio.run(generate_email(b"bytes", "image/png", None, make_settings()))


@patch("backend.services.generate_email.extract_color_style")
@patch("backend.services.generate_email.extract_layout")
def test_generate_email_wraps_color_style_failure(mock_layout, mock_styles):
    from backend.services.color_style import ColorStyleExtractionError

    mock_layout.return_value = make_layout(BlockType.HEADER)
    mock_styles.side_effect = ColorStyleExtractionError("boom")

    with pytest.raises(GenerateEmailError):
        asyncio.run(generate_email(b"bytes", "image/png", None, make_settings()))
