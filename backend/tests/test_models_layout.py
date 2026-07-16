import pytest
from pydantic import ValidationError

from backend.models.layout import BlockType, BoundingBox, LayoutBlock, LayoutExtractionResult


def test_bounding_box_valid():
    box = BoundingBox(ymin=0, xmin=0, ymax=500, xmax=500)
    assert box.ymax == 500


def test_bounding_box_rejects_inverted_y():
    with pytest.raises(ValidationError):
        BoundingBox(ymin=500, xmin=0, ymax=100, xmax=500)


def test_bounding_box_rejects_inverted_x():
    with pytest.raises(ValidationError):
        BoundingBox(ymin=0, xmin=500, ymax=500, xmax=100)


def test_bounding_box_rejects_out_of_range():
    with pytest.raises(ValidationError):
        BoundingBox(ymin=0, xmin=0, ymax=500, xmax=1500)


def test_layout_block_sanitizes_text():
    block = LayoutBlock(
        type=BlockType.PARAGRAPH,
        box=BoundingBox(ymin=0, xmin=0, ymax=100, xmax=100),
        text="<b>Hello</b> <script>alert(1)</script>",
    )
    assert block.text == "Hello alert(1)"
    assert "<" not in block.text and ">" not in block.text


def test_layout_block_defaults_empty_text():
    block = LayoutBlock(
        type=BlockType.IMAGE,
        box=BoundingBox(ymin=0, xmin=0, ymax=100, xmax=100),
    )
    assert block.text == ""


def test_layout_extraction_result_defaults():
    result = LayoutExtractionResult(
        blocks=[
            LayoutBlock(
                type=BlockType.OTHER,
                box=BoundingBox(ymin=0, xmin=0, ymax=1000, xmax=1000),
            )
        ],
        model="gemini-2.5-flash",
    )
    assert result.degraded is False
    assert len(result.blocks) == 1
