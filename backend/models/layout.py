from enum import StrEnum

import bleach
from pydantic import BaseModel, Field, field_validator, model_validator


class BlockType(StrEnum):
    HEADER = "header"
    PARAGRAPH = "paragraph"
    IMAGE = "image"
    BUTTON = "button"
    FOOTER = "footer"
    HERO = "hero"
    DIVIDER = "divider"
    OTHER = "other"


class BoundingBox(BaseModel):
    ymin: int = Field(ge=0, le=1000)
    xmin: int = Field(ge=0, le=1000)
    ymax: int = Field(ge=0, le=1000)
    xmax: int = Field(ge=0, le=1000)

    @model_validator(mode="after")
    def check_ordering(self) -> "BoundingBox":
        if self.ymin >= self.ymax:
            raise ValueError("ymin must be less than ymax")
        if self.xmin >= self.xmax:
            raise ValueError("xmin must be less than xmax")
        return self


class LayoutBlock(BaseModel):
    type: BlockType
    box: BoundingBox
    text: str = ""

    @field_validator("text")
    @classmethod
    def sanitize_text(cls, value: str) -> str:
        return bleach.clean(value, tags=[], attributes={}, strip=True)


class LayoutExtractionResult(BaseModel):
    blocks: list[LayoutBlock]
    degraded: bool = False
    model: str
