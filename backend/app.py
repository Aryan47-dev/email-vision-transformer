from fastapi import FastAPI

from backend.api.layout_extraction import router as layout_extraction_router
from backend.api.ocr_extraction import router as ocr_extraction_router

app = FastAPI(title="Email Vision Transformer API")

app.include_router(layout_extraction_router)
app.include_router(ocr_extraction_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
