import asyncio

from backend.config import Settings
from backend.html_generator.builder import build_email_html
from backend.models.generate_email import GenerateEmailResult
from backend.models.layout import BlockType, LayoutExtractionResult
from backend.services.color_style import ColorStyleExtractionError, extract_color_style
from backend.services.layout_extraction import LayoutExtractionError, extract_layout


class GenerateEmailError(Exception):
    pass


def _build_assets_map(
    layout: LayoutExtractionResult, asset_urls: list[str] | None
) -> dict[int, str]:
    if not asset_urls:
        return {}

    image_indices = [
        index for index, block in enumerate(layout.blocks) if block.type == BlockType.IMAGE
    ]

    return dict(zip(image_indices, asset_urls))


async def generate_email(
    image_bytes: bytes,
    mime_type: str,
    asset_urls: list[str] | None,
    settings: Settings,
) -> GenerateEmailResult:
    try:
        layout, styles = await asyncio.gather(
            asyncio.to_thread(extract_layout, image_bytes, mime_type, settings),
            asyncio.to_thread(extract_color_style, image_bytes, mime_type, settings),
        )
    except (LayoutExtractionError, ColorStyleExtractionError) as exc:
        raise GenerateEmailError(str(exc)) from exc

    assets = _build_assets_map(layout, asset_urls)
    html = build_email_html(layout, styles, assets)

    return GenerateEmailResult(html=html)
