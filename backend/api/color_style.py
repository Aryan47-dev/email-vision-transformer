from fastapi import APIRouter, Depends, HTTPException, UploadFile

from backend.config import Settings, get_settings
from backend.models.color_style import ColorStyleResult
from backend.services.color_style import ColorStyleExtractionError, extract_color_style

router = APIRouter(prefix="/api", tags=["color-style"])


@router.post("/color-style", response_model=ColorStyleResult)
async def color_style(
    image: UploadFile,
    settings: Settings = Depends(get_settings),
) -> ColorStyleResult:
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")

    image_bytes = await image.read()

    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty")

    if len(image_bytes) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Uploaded image is too large")

    try:
        return extract_color_style(image_bytes, image.content_type, settings)
    except ColorStyleExtractionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
