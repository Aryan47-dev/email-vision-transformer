from backend.models.layout import BoundingBox
from backend.models.ocr import OcrBlock, OcrExtractionResult


def test_ocr_block_sanitizes_text():
    block = OcrBlock(
        text="<b>Hello</b> <script>alert(1)</script>",
        box=BoundingBox(ymin=0, xmin=0, ymax=100, xmax=100),
    )
    assert block.text == "Hello alert(1)"
    assert "<" not in block.text and ">" not in block.text


def test_ocr_extraction_result_defaults():
    result = OcrExtractionResult()
    assert result.full_text == ""
    assert result.blocks == []


def test_ocr_extraction_result_sanitizes_full_text():
    result = OcrExtractionResult(full_text="<script>alert(1)</script>Hi there")
    assert result.full_text == "alert(1)Hi there"
    assert "<" not in result.full_text and ">" not in result.full_text


def test_ocr_extraction_result_with_blocks():
    result = OcrExtractionResult(
        full_text="Hello World",
        blocks=[
            OcrBlock(text="Hello", box=BoundingBox(ymin=0, xmin=0, ymax=100, xmax=200)),
            OcrBlock(text="World", box=BoundingBox(ymin=0, xmin=210, ymax=100, xmax=400)),
        ],
    )
    assert len(result.blocks) == 2
    assert result.blocks[0].text == "Hello"
