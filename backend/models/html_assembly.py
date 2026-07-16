from pydantic import BaseModel, field_validator

from backend.models.color_style import ColorStyleResult
from backend.models.layout import LayoutExtractionResult

_ALLOWED_URL_SCHEMES = ("http://", "https://")


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
            if not url.startswith(_ALLOWED_URL_SCHEMES):
                raise ValueError(f"{url!r} must be an http:// or https:// URL")
        return value


class HtmlAssemblyResult(BaseModel):
    html: str
