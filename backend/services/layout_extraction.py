from google import genai
from google.genai import types
from pydantic import TypeAdapter

from backend.config import Settings
from backend.models.layout import BoundingBox, LayoutBlock, LayoutExtractionResult
from prompts.layout_extraction import RETRY_REMINDER, SYSTEM_INSTRUCTION, USER_PROMPT

_BLOCKS_ADAPTER = TypeAdapter(list[LayoutBlock])

_FULL_IMAGE_BOX = BoundingBox(ymin=0, xmin=0, ymax=1000, xmax=1000)


class LayoutExtractionError(Exception):
    pass


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
        ),
    )

    if response.parsed:
        return _BLOCKS_ADAPTER.validate_python(response.parsed)

    if response.text:
        return _BLOCKS_ADAPTER.validate_json(response.text)

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

    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

    for prompt in (USER_PROMPT, f"{USER_PROMPT}\n\n{RETRY_REMINDER}"):
        try:
            blocks = _call_gemini(client, settings, image_part, prompt)
        except Exception:
            blocks = None

        if blocks:
            return LayoutExtractionResult(
                blocks=blocks, degraded=False, model=settings.gemini_model
            )

    fallback_block = LayoutBlock(type="other", box=_FULL_IMAGE_BOX, text="")
    return LayoutExtractionResult(
        blocks=[fallback_block], degraded=True, model=settings.gemini_model
    )
