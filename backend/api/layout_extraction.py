from fastapi import APIRouter, Depends, HTTPException, UploadFile

from backend.config import Settings, get_settings
from backend.models.layout import LayoutExtractionResult
from backend.services.layout_extraction import LayoutExtractionError, extract_layout

router = APIRouter(prefix="/api", tags=["layout-extraction"])


@router.post("/layout-extraction", response_model=LayoutExtractionResult)
async def layout_extraction(
    image: UploadFile,
    settings: Settings = Depends(get_settings),
) -> LayoutExtractionResult:
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")

    image_bytes = await image.read()

    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty")

    if len(image_bytes) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Uploaded image is too large")

    try:
        return extract_layout(image_bytes, image.content_type, settings)
    except LayoutExtractionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
