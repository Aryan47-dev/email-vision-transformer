import re

from pydantic import BaseModel, field_validator

from backend.models.color_style import ColorStyleResult
from backend.models.layout import LayoutExtractionResult

_ALLOWED_URL_SCHEMES = ("http://", "https://")

# Deliberately excludes image/svg+xml: SVGs can embed <script> tags that
# execute when rendered in some contexts, unlike raster formats.
_ALLOWED_DATA_IMAGE_RE = re.compile(
    r"^data:image/(png|jpeg|jpg|webp|gif);base64,", re.IGNORECASE
)


class HtmlAssemblyRequest(BaseModel):
    layout: LayoutExtractionResult
    styles: ColorStyleResult
    assets: dict[int, str] | None = None

    @field_validator("assets")
    @classmethod
    def validate_asset_urls(cls, value: dict[int, str] | None) -> dict[int, str] | None:
        if value is None:
            return value
        for url in value.values():
            if url.startswith(_ALLOWED_URL_SCHEMES):
                continue
            if _ALLOWED_DATA_IMAGE_RE.match(url):
                continue
            raise ValueError(
                f"{url!r} must be an http:// or https:// URL, or a "
                "data:image/(png|jpeg|webp|gif);base64,... URI"
            )
        return value


class HtmlAssemblyResult(BaseModel):
    html: str
