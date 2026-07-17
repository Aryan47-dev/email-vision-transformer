from google import genai
from google.genai import types
from pydantic import TypeAdapter

from backend.config import Settings
from backend.models.ocr import OcrBlock, OcrExtractionResult
from prompts.ocr_extraction import RETRY_REMINDER, SYSTEM_INSTRUCTION, USER_PROMPT

_BLOCKS_ADAPTER = TypeAdapter(list[OcrBlock])


class OcrExtractionError(Exception):
    pass


def _call_gemini(
    client: genai.Client,
    settings: Settings,
    image_part: types.Part,
    prompt: str,
) -> list[OcrBlock] | None:
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=[image_part, prompt],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=list[OcrBlock],
        ),
    )

    if response.parsed is not None:
        return _BLOCKS_ADAPTER.validate_python(response.parsed)

    if response.text:
        return _BLOCKS_ADAPTER.validate_json(response.text)

    return None


def extract_text(image_bytes: bytes, mime_type: str, settings: Settings) -> OcrExtractionResult:
    if not settings.google_api_key:
        raise OcrExtractionError("GOOGLE_API_KEY is not configured")

    try:
        client = genai.Client(api_key=settings.google_api_key)
    except Exception as exc:
        raise OcrExtractionError(f"Failed to initialize Gemini client: {exc}") from exc

    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

    for prompt in (USER_PROMPT, f"{USER_PROMPT}\n\n{RETRY_REMINDER}"):
        try:
            blocks = _call_gemini(client, settings, image_part, prompt)
        except Exception:
            blocks = None

        if blocks is not None:
            full_text = "\n".join(block.text for block in blocks if block.text)
            return OcrExtractionResult(full_text=full_text, blocks=blocks)

    return OcrExtractionResult(full_text="", blocks=[])
