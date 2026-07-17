import io

from google import genai
from google.genai import types
from PIL import Image
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


def _hex_from_rgb(r: int, g: int, b: int) -> str:
    return f"#{r:02X}{g:02X}{b:02X}"


def _local_color_fallback(image_bytes: bytes) -> ColorStyleResult:
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            rgb_img = img.convert("RGB")
            rgb_img.thumbnail((150, 150))
            paletted = rgb_img.quantize(colors=8)
            palette = paletted.getpalette()
            color_counts = sorted(paletted.getcolors(), reverse=True)
    except Exception as exc:
        raise ColorStyleExtractionError(f"Failed to analyze image locally: {exc}") from exc

    hex_colors = [
        _hex_from_rgb(*palette[index * 3 : index * 3 + 3]) for _, index in color_counts[:3]
    ]
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
        source="local_fallback",
    )


def extract_color_style(
    image_bytes: bytes, mime_type: str, settings: Settings
) -> ColorStyleResult:
    fields = _try_gemini(image_bytes, mime_type, settings)
    if fields:
        return ColorStyleResult(**fields.model_dump(), degraded=False, source="gemini")

    return _local_color_fallback(image_bytes)
