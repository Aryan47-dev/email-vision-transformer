from unittest.mock import patch

import pytest
from jinja2 import TemplateError

from backend.models.color_style import ColorStyleResult
from backend.models.html_assembly import HtmlAssemblyRequest
from backend.models.layout import BlockType, BoundingBox, LayoutBlock, LayoutExtractionResult
from backend.services.html_assembly import HtmlAssemblyError, assemble_html


def make_request() -> HtmlAssemblyRequest:
    return HtmlAssemblyRequest(
        layout=LayoutExtractionResult(
            blocks=[
                LayoutBlock(
                    type=BlockType.HEADER,
                    box=BoundingBox(ymin=0, xmin=0, ymax=100, xmax=1000),
                    text="Welcome",
                )
            ],
            model="gemini-test",
        ),
        styles=ColorStyleResult(
            bg_color="#FFFFFF",
            heading_color="#000000",
            link_color="#0000FF",
            heading_font="sans-serif bold",
            body_font="sans-serif regular",
            body_font_size="14px",
            source="gemini",
        ),
    )


def test_assemble_html_delegates_to_builder():
    result = assemble_html(make_request())

    assert "Welcome" in result.html
    assert "<table" in result.html


def test_assemble_html_wraps_template_errors():
    with patch(
        "backend.services.html_assembly.build_email_html",
        side_effect=TemplateError("boom"),
    ):
        with pytest.raises(HtmlAssemblyError):
            assemble_html(make_request())
