import bleach
from pydantic import BaseModel, field_validator

from backend.models.layout import BoundingBox


class OcrBlock(BaseModel):
    text: str
    box: BoundingBox

    @field_validator("text")
    @classmethod
    def sanitize_text(cls, value: str) -> str:
        return bleach.clean(value, tags=[], attributes={}, strip=True)


class OcrExtractionResult(BaseModel):
    full_text: str = ""
    blocks: list[OcrBlock] = []

    @field_validator("full_text")
    @classmethod
    def sanitize_full_text(cls, value: str) -> str:
        return bleach.clean(value, tags=[], attributes={}, strip=True)
