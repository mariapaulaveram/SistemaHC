import json
from typing import Any
from fastapi import Request, Response
from fastapi.templating import Jinja2Templates

FLASH_COOKIE = "flash_messages"


def get_flash_messages(request: Request) -> list[str]:
    raw = request.cookies.get(FLASH_COOKIE)
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
        return [str(parsed)]
    except (ValueError, TypeError):
        return []


def render_template(templates: Jinja2Templates, request: Request, name: str, context: dict[str, Any] | None = None):
    context = context or {}
    if "flash_messages" not in context:
        context["flash_messages"] = get_flash_messages(request)
    response = templates.TemplateResponse(request=request, name=name, context=context)
    response.delete_cookie(FLASH_COOKIE, path="/")
    return response


def set_flash_message(response: Response, message: str):
    response.set_cookie(FLASH_COOKIE, json.dumps([message]), path="/", max_age=30)
