from jinja2 import TemplateError

from backend.html_generator.builder import build_email_html
from backend.models.html_assembly import HtmlAssemblyRequest, HtmlAssemblyResult


class HtmlAssemblyError(Exception):
    pass


def assemble_html(request: HtmlAssemblyRequest) -> HtmlAssemblyResult:
    try:
        html = build_email_html(request.layout, request.styles, request.assets)
    except TemplateError as exc:
        raise HtmlAssemblyError(f"Failed to render email template: {exc}") from exc

    return HtmlAssemblyResult(html=html)
