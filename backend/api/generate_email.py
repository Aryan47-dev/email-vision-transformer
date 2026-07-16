from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from pydantic import TypeAdapter, ValidationError

from backend.config import Settings, get_settings
from backend.models.generate_email import GenerateEmailResult
from backend.services.generate_email import GenerateEmailError, generate_email

router = APIRouter(prefix="/api", tags=["generate-email"])

_ASSETS_ADAPTER = TypeAdapter(list[str])


def _parse_assets(assets: str | None) -> list[str] | None:
    if assets is None:
        return None

    try:
        return _ASSETS_ADAPTER.validate_json(assets)
    except ValidationError as exc:
        raise HTTPException(
            status_code=400, detail="assets must be a JSON array of URL strings"
        ) from exc


@router.post("/generate-email", response_model=GenerateEmailResult)
async def generate_email_route(
    image: UploadFile,
    assets: str | None = Form(None),
    settings: Settings = Depends(get_settings),
) -> GenerateEmailResult:
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")

    image_bytes = await image.read()

    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty")

    if len(image_bytes) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Uploaded image is too large")

    asset_urls = _parse_assets(assets)

    try:
        return await generate_email(image_bytes, image.content_type, asset_urls, settings)
    except GenerateEmailError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
