import io
import logging

from google import genai
from google.genai import types
from PIL import Image
from pydantic import TypeAdapter, ValidationError

from backend.config import Settings
from backend.models.layout import BoundingBox, LayoutBlock, LayoutExtractionResult
from prompts.layout_extraction import RETRY_REMINDER, SYSTEM_INSTRUCTION, USER_PROMPT

logger = logging.getLogger(__name__)

_BLOCKS_ADAPTER = TypeAdapter(list[LayoutBlock])

_FULL_IMAGE_BOX = BoundingBox(ymin=0, xmin=0, ymax=1000, xmax=1000)

# Generous ceiling for structured JSON output describing a content-dense layout
# (many sections/blocks). The SDK default can be too low for this and silently
# truncate the response, producing unparseable JSON.
_MAX_OUTPUT_TOKENS = 8192

# Very large screenshots (long scrolling captures especially) are downscaled
# before being sent to Gemini, per the design doc's own performance guidance.
_MAX_IMAGE_DIMENSION = 2048


class LayoutExtractionError(Exception):
    pass


def _downscale_if_needed(image_bytes: bytes, mime_type: str) -> tuple[bytes, str]:
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            if max(img.size) <= _MAX_IMAGE_DIMENSION:
                return image_bytes, mime_type

            resized = img.convert("RGB")
            resized.thumbnail((_MAX_IMAGE_DIMENSION, _MAX_IMAGE_DIMENSION))
            buf = io.BytesIO()
            resized.save(buf, format="PNG")
            return buf.getvalue(), "image/png"
    except Exception:
        logger.warning("layout-extraction: failed to downscale image, using original", exc_info=True)
        return image_bytes, mime_type


def _call_gemini(
    client: genai.Client,
    settings: Settings,
    image_part: types.Part,
    prompt: str,
) -> list[LayoutBlock] | None:
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=[image_part, prompt],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=list[LayoutBlock],
            max_output_tokens=_MAX_OUTPUT_TOKENS,
        ),
    )

    finish_reason = None
    if response.candidates:
        finish_reason = response.candidates[0].finish_reason

    if response.parsed:
        try:
            return _BLOCKS_ADAPTER.validate_python(response.parsed)
        except ValidationError as exc:
            logger.warning(
                "layout-extraction: response.parsed failed schema validation "
                "(finish_reason=%s): %s",
                finish_reason,
                exc,
            )

    if response.text:
        try:
            return _BLOCKS_ADAPTER.validate_json(response.text)
        except ValidationError as exc:
            logger.warning(
                "layout-extraction: response.text failed JSON/schema validation "
                "(finish_reason=%s, length=%d): %s | text snippet: %r",
                finish_reason,
                len(response.text),
                exc,
                response.text[-300:],
            )

    logger.warning(
        "layout-extraction: no usable output from Gemini (finish_reason=%s, "
        "has_parsed=%s, has_text=%s)",
        finish_reason,
        bool(response.parsed),
        bool(response.text),
    )
    return None


def extract_layout(
    image_bytes: bytes, mime_type: str, settings: Settings
) -> LayoutExtractionResult:
    if not settings.google_api_key:
        raise LayoutExtractionError("GOOGLE_API_KEY is not configured")

    try:
        client = genai.Client(api_key=settings.google_api_key)
    except Exception as exc:
        raise LayoutExtractionError(f"Failed to initialize Gemini client: {exc}") from exc

    request_bytes, request_mime_type = _downscale_if_needed(image_bytes, mime_type)
    image_part = types.Part.from_bytes(data=request_bytes, mime_type=request_mime_type)

    for attempt, prompt in enumerate((USER_PROMPT, f"{USER_PROMPT}\n\n{RETRY_REMINDER}"), start=1):
        try:
            blocks = _call_gemini(client, settings, image_part, prompt)
        except Exception:
            logger.warning("layout-extraction: attempt %d raised an exception", attempt, exc_info=True)
            blocks = None

        if blocks:
            return LayoutExtractionResult(
                blocks=blocks, degraded=False, model=settings.gemini_model
            )

    logger.warning(
        "layout-extraction: both attempts failed, degrading to a single "
        "image block referencing the original upload"
    )
    # Matches the design doc's own stated last resort: "treat the entire
    # preview as one block and output a single <img> placeholder". The
    # orchestration layer (generate-email service / frontend) is responsible
    # for supplying the actual uploaded image as this block's asset, since
    # this function has no visibility into how the asset-URL mapping will be
    # built downstream.
    fallback_block = LayoutBlock(
        type="image", box=_FULL_IMAGE_BOX, text="Original design (could not be segmented)"
    )
    return LayoutExtractionResult(
        blocks=[fallback_block], degraded=True, model=settings.gemini_model
    )
