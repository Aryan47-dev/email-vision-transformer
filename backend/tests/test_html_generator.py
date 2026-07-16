from backend.html_generator.builder import build_email_html
from backend.models.color_style import ColorStyleResult
from backend.models.layout import BlockType, BoundingBox, LayoutBlock, LayoutExtractionResult


def make_box() -> BoundingBox:
    return BoundingBox(ymin=0, xmin=0, ymax=100, xmax=1000)


def make_styles() -> ColorStyleResult:
    return ColorStyleResult(
        bg_color="#FFFFFF",
        heading_color="#111111",
        link_color="#0000FF",
        heading_font="sans-serif bold",
        body_font="sans-serif regular",
        body_font_size="14px",
        source="gemini",
    )


def make_layout(blocks: list[LayoutBlock]) -> LayoutExtractionResult:
    return LayoutExtractionResult(blocks=blocks, model="gemini-test")


def test_renders_table_and_mso_and_media_query():
    layout = make_layout(
        [LayoutBlock(type=BlockType.HEADER, box=make_box(), text="Welcome")]
    )
    html = build_email_html(layout, make_styles())

    assert "<table" in html
    assert "<!--[if mso]>" in html
    assert "@media only screen and (max-width: 600px)" in html


def test_header_uses_heading_color_and_font():
    layout = make_layout(
        [LayoutBlock(type=BlockType.HEADER, box=make_box(), text="Welcome")]
    )
    html = build_email_html(layout, make_styles())

    assert "color:#111111" in html
    assert "sans-serif bold" in html
    assert "Welcome" in html


def test_paragraph_uses_body_font_size():
    layout = make_layout(
        [LayoutBlock(type=BlockType.PARAGRAPH, box=make_box(), text="Body copy")]
    )
    html = build_email_html(layout, make_styles())

    assert "font-size:14px" in html
    assert "Body copy" in html


def test_image_uses_placeholder_when_no_asset_supplied():
    layout = make_layout(
        [LayoutBlock(type=BlockType.IMAGE, box=make_box(), text="Logo")]
    )
    html = build_email_html(layout, make_styles())

    assert "via.placeholder.com" in html
    assert 'alt="Logo"' in html


def test_image_uses_supplied_asset_url():
    layout = make_layout(
        [LayoutBlock(type=BlockType.IMAGE, box=make_box(), text="Logo")]
    )
    html = build_email_html(
        layout, make_styles(), assets={0: "https://example.com/logo.png"}
    )

    assert "https://example.com/logo.png" in html
    assert "via.placeholder.com" not in html


def test_button_renders_link_color_and_text():
    layout = make_layout(
        [LayoutBlock(type=BlockType.BUTTON, box=make_box(), text="Buy Now")]
    )
    html = build_email_html(layout, make_styles())

    assert "background-color:#0000FF" in html
    assert "Buy Now" in html


def test_divider_renders_hr():
    layout = make_layout([LayoutBlock(type=BlockType.DIVIDER, box=make_box())])
    html = build_email_html(layout, make_styles())

    assert "<hr" in html


def test_ampersand_is_escaped_exactly_once():
    layout = make_layout(
        [LayoutBlock(type=BlockType.PARAGRAPH, box=make_box(), text="Terms & Conditions")]
    )
    html = build_email_html(layout, make_styles())

    assert "Terms &amp; Conditions" in html
    assert "&amp;amp;" not in html


def test_empty_blocks_still_renders_shell():
    layout = make_layout([])
    html = build_email_html(layout, make_styles())

    assert "<table" in html
    assert "<!DOCTYPE html>" in html
