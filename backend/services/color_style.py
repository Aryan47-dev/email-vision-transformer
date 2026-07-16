from google import genai
from google.api_core.client_options import ClientOptions
from google.cloud import vision
from google.genai import types
from pydantic import TypeAdapter, ValidationError

from backend.config import Settings
from backend.models.color_style import ColorStyleFields, ColorStyleResult
from prompts.color_style import RETRY_REMINDER, SYSTEM_INSTRUCTION, USER_PROMPT

_FIELDS_ADAPTER = TypeAdapter(ColorStyleFields)

_FALLBACK_HEADING_FONT = "sans-serif bold"
_FALLBACK_BODY_FONT = "sans-serif regular"
_FALLBACK_BODY_FONT_SIZE = "14px"
_FALLBACK_BG_COLOR = "#FFFFFF"
_FALLBACK_TEXT_COLOR = "#000000"


class ColorStyleExtractionError(Exception):
    pass


def _call_gemini(
    client: genai.Client,
    settings: Settings,
    image_part: types.Part,
    prompt: str,
) -> ColorStyleFields | None:
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=[image_part, prompt],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=ColorStyleFields,
        ),
    )

    if response.parsed:
        try:
            return _FIELDS_ADAPTER.validate_python(response.parsed)
        except ValidationError:
            pass

    if response.text:
        try:
            return _FIELDS_ADAPTER.validate_json(response.text)
        except ValidationError:
            pass

    return None


def _try_gemini(
    image_bytes: bytes, mime_type: str, settings: Settings
) -> ColorStyleFields | None:
    if not settings.google_api_key:
        return None

    try:
        client = genai.Client(api_key=settings.google_api_key)
    except Exception:
        return None

    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

    for prompt in (USER_PROMPT, f"{USER_PROMPT}\n\n{RETRY_REMINDER}"):
        try:
            fields = _call_gemini(client, settings, image_part, prompt)
        except Exception:
            fields = None

        if fields:
            return fields

    return None


def _hex_from_rgb(color) -> str:
    r, g, b = color.red, color.green, color.blue
    # Cloud Vision's image_properties returns 0-255 in practice, despite the
    # google.type.Color proto documenting a [0, 1] range - normalize defensively.
    if max(r, g, b) <= 1.0:
        r, g, b = r * 255, g * 255, b * 255

    r = max(0, min(255, round(r)))
    g = max(0, min(255, round(g)))
    b = max(0, min(255, round(b)))
    return f"#{r:02X}{g:02X}{b:02X}"


def _vision_fallback(image_bytes: bytes, settings: Settings) -> ColorStyleResult:
    if not settings.google_cloud_vision_api_key:
        raise ColorStyleExtractionError("GOOGLE_CLOUD_VISION_API_KEY is not configured")

    try:
        client = vision.ImageAnnotatorClient(
            client_options=ClientOptions(api_key=settings.google_cloud_vision_api_key)
        )
        response = client.image_properties(image=vision.Image(content=image_bytes))
    except Exception as exc:
        raise ColorStyleExtractionError(f"Vision image_properties failed: {exc}") from exc

    if response.error and response.error.message:
        raise ColorStyleExtractionError(response.error.message)

    colors = sorted(
        response.image_properties_annotation.dominant_colors.colors,
        key=lambda c: c.pixel_fraction,
        reverse=True,
    )

    hex_colors = [_hex_from_rgb(c.color) for c in colors[:3]]
    while len(hex_colors) < 3:
        hex_colors.append(_FALLBACK_BG_COLOR if not hex_colors else _FALLBACK_TEXT_COLOR)

    bg_color, heading_color, link_color = hex_colors[0], hex_colors[1], hex_colors[2]

    return ColorStyleResult(
        bg_color=bg_color,
        heading_color=heading_color,
        link_color=link_color,
        heading_font=_FALLBACK_HEADING_FONT,
        body_font=_FALLBACK_BODY_FONT,
        body_font_size=_FALLBACK_BODY_FONT_SIZE,
        degraded=True,
        source="vision_fallback",
    )


def extract_color_style(
    image_bytes: bytes, mime_type: str, settings: Settings
) -> ColorStyleResult:
    fields = _try_gemini(image_bytes, mime_type, settings)
    if fields:
        return ColorStyleResult(**fields.model_dump(), degraded=False, source="gemini")

    return _vision_fallback(image_bytes, settings)
