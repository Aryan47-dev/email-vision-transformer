from fastapi import APIRouter, HTTPException

from backend.models.html_assembly import HtmlAssemblyRequest, HtmlAssemblyResult
from backend.services.html_assembly import HtmlAssemblyError, assemble_html

router = APIRouter(prefix="/api", tags=["html-assembly"])


@router.post("/html-assembly", response_model=HtmlAssemblyResult)
async def html_assembly(request: HtmlAssemblyRequest) -> HtmlAssemblyResult:
    try:
        return assemble_html(request)
    except HtmlAssemblyError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
