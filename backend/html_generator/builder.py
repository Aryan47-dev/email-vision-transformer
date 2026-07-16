import html
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from backend.models.color_style import ColorStyleResult
from backend.models.layout import BlockType, LayoutBlock, LayoutExtractionResult

_TEMPLATES_DIR = Path(__file__).parent / "templates"

_ENV = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["jinja", "html"]),
)

_BODY_TEXT_COLOR = "#333333"
_HEADING_FONT_SIZE = "24px"
_FOOTER_FONT_SIZE = "12px"
_DIVIDER_COLOR = "#DDDDDD"
_PLACEHOLDER_IMAGE_URL = "https://via.placeholder.com/600x200?text=Image"


def _plain_text(text: str) -> str:
    # LayoutBlock.text was already HTML-escaped by bleach.clean() at the model
    # layer (e.g. "&" -> "&amp;"). Jinja2's autoescape will escape it again on
    # render, so unescape here first to avoid double-escaping ("&amp;amp;").
    return html.unescape(text)


def _build_block(index: int, block: LayoutBlock, styles: ColorStyleResult, assets: dict) -> dict:
    text = _plain_text(block.text)

    if block.type in (BlockType.HEADER, BlockType.HERO):
        return {
            "render_type": "text",
            "text": text,
            "color": styles.heading_color,
            "font_family": styles.heading_font,
            "font_size": _HEADING_FONT_SIZE,
            "align": "left",
        }

    if block.type == BlockType.FOOTER:
        return {
            "render_type": "text",
            "text": text,
            "color": _BODY_TEXT_COLOR,
            "font_family": styles.body_font,
            "font_size": _FOOTER_FONT_SIZE,
            "align": "center",
        }

    if block.type == BlockType.BUTTON:
        return {
            "render_type": "button",
            "text": text or "Click Here",
            "bg_color": styles.link_color,
            "font_family": styles.body_font,
        }

    if block.type == BlockType.IMAGE:
        return {
            "render_type": "image",
            "src": assets.get(index, _PLACEHOLDER_IMAGE_URL),
            "alt": text or "Image",
        }

    if block.type == BlockType.DIVIDER:
        return {"render_type": "divider", "color": _DIVIDER_COLOR}

    # PARAGRAPH, OTHER, and any future/unknown types default to body text
    return {
        "render_type": "text",
        "text": text,
        "color": _BODY_TEXT_COLOR,
        "font_family": styles.body_font,
        "font_size": styles.body_font_size,
        "align": "left",
    }


def build_email_html(
    layout: LayoutExtractionResult,
    styles: ColorStyleResult,
    assets: dict[int, str] | None = None,
) -> str:
    assets = assets or {}
    blocks = [
        _build_block(index, block, styles, assets)
        for index, block in enumerate(layout.blocks)
    ]

    template = _ENV.get_template("email.html.jinja")
    return template.render(bg_color=styles.bg_color, blocks=blocks)
