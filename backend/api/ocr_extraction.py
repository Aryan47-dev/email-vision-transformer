from fastapi import APIRouter, Depends, HTTPException, UploadFile

from backend.config import Settings, get_settings
from backend.models.ocr import OcrExtractionResult
from backend.services.ocr_extraction import OcrExtractionError, extract_text

router = APIRouter(prefix="/api", tags=["ocr-extraction"])


@router.post("/ocr-extraction", response_model=OcrExtractionResult)
async def ocr_extraction(
    image: UploadFile,
    settings: Settings = Depends(get_settings),
) -> OcrExtractionResult:
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")

    image_bytes = await image.read()

    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty")

    if len(image_bytes) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Uploaded image is too large")

    try:
        return extract_text(image_bytes, settings)
    except OcrExtractionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
