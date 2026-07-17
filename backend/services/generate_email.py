import asyncio
import base64
import io
import logging

from PIL import Image

from backend.config import Settings
from backend.html_generator.builder import build_email_html
from backend.models.generate_email import GenerateEmailResult
from backend.models.layout import BlockType, LayoutExtractionResult
from backend.services.color_style import ColorStyleExtractionError, extract_color_style
from backend.services.layout_extraction import LayoutExtractionError, extract_layout

logger = logging.getLogger(__name__)


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


def _image_data_uri(image_bytes: bytes) -> str:
    # Re-encode to PNG so the mime type always matches what
    # HtmlAssemblyRequest's data-URI validator allows, regardless of the
    # original upload's format.
    with Image.open(io.BytesIO(image_bytes)) as img:
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _apply_degraded_fallback_asset(
    layout: LayoutExtractionResult, assets: dict[int, str], image_bytes: bytes
) -> dict[int, str]:
    # If layout-extraction couldn't segment the image, it returns a single
    # image-type block covering the whole design. Show the caller's actual
    # upload there instead of a generic placeholder - unless the caller
    # already supplied their own asset for that slot.
    if layout.degraded and 0 not in assets:
        try:
            assets = {**assets, 0: _image_data_uri(image_bytes)}
        except Exception:
            logger.warning(
                "generate-email: failed to embed original image for degraded "
                "fallback, using placeholder instead",
                exc_info=True,
            )
    return assets


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
    assets = _apply_degraded_fallback_asset(layout, assets, image_bytes)
    html = build_email_html(layout, styles, assets)

    return GenerateEmailResult(html=html)
