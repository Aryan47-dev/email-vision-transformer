import io

from google.api_core.client_options import ClientOptions
from google.cloud import vision
from PIL import Image

from backend.config import Settings
from backend.models.layout import BoundingBox
from backend.models.ocr import OcrBlock, OcrExtractionResult


class OcrExtractionError(Exception):
    pass


def _scale(value: float, size: int) -> int:
    if size <= 0:
        return 0
    return max(0, min(1000, round(value / size * 1000)))


def _vertices_to_box(vertices, width: int, height: int) -> BoundingBox:
    xs = [v.x for v in vertices]
    ys = [v.y for v in vertices]

    xmin = _scale(min(xs), width)
    xmax = _scale(max(xs), width)
    ymin = _scale(min(ys), height)
    ymax = _scale(max(ys), height)

    if xmax <= xmin:
        xmax = min(1000, xmin + 1)
    if ymax <= ymin:
        ymax = min(1000, ymin + 1)

    return BoundingBox(ymin=ymin, xmin=xmin, ymax=ymax, xmax=xmax)


def _call_vision(client: vision.ImageAnnotatorClient, image_bytes: bytes):
    response = client.text_detection(image=vision.Image(content=image_bytes))
    if response.error and response.error.message:
        raise OcrExtractionError(response.error.message)
    return response


def extract_text(image_bytes: bytes, settings: Settings) -> OcrExtractionResult:
    if not settings.google_cloud_vision_api_key:
        raise OcrExtractionError("GOOGLE_CLOUD_VISION_API_KEY is not configured")

    try:
        client = vision.ImageAnnotatorClient(
            client_options=ClientOptions(api_key=settings.google_cloud_vision_api_key)
        )
    except Exception as exc:
        raise OcrExtractionError(f"Failed to initialize Vision client: {exc}") from exc

    response = None
    last_error: Exception | None = None
    for _ in range(2):
        try:
            response = _call_vision(client, image_bytes)
            break
        except Exception as exc:
            last_error = exc
            response = None

    if response is None:
        raise OcrExtractionError(f"Vision text detection failed: {last_error}")

    annotations = list(response.text_annotations)
    if not annotations:
        return OcrExtractionResult(full_text="", blocks=[])

    full_text = annotations[0].description or ""

    with Image.open(io.BytesIO(image_bytes)) as img:
        width, height = img.size

    blocks = [
        OcrBlock(
            text=annotation.description or "",
            box=_vertices_to_box(annotation.bounding_poly.vertices, width, height),
        )
        for annotation in annotations[1:]
    ]

    return OcrExtractionResult(full_text=full_text, blocks=blocks)
