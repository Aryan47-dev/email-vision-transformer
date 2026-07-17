import re
from typing import Literal

from pydantic import BaseModel, field_validator

_HEX_COLOR_RE = re.compile(r"^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$")


class ColorStyleFields(BaseModel):
    bg_color: str
    heading_color: str
    link_color: str
    heading_font: str
    body_font: str
    body_font_size: str

    @field_validator("bg_color", "heading_color", "link_color")
    @classmethod
    def validate_hex_color(cls, value: str) -> str:
        if not _HEX_COLOR_RE.match(value):
            raise ValueError(f"{value!r} is not a valid hex color")
        return value


class ColorStyleResult(ColorStyleFields):
    degraded: bool = False
    source: Literal["gemini", "local_fallback"]
