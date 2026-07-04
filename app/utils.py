import json
from datetime import date
from typing import Any
from fastapi import Request, Response, HTTPException
from fastapi.templating import Jinja2Templates
from .auth import get_current_user_id, create_csrf_token, verify_csrf_token, is_admin as _is_admin

FLASH_COOKIE = "flash_messages"


# ── Filtros Jinja2 compartidos ────────────────────────────────────────────────

def _calcular_edad(fecha_nacimiento):
    if not fecha_nacimiento:
        return None
    hoy = date.today()
    return hoy.year - fecha_nacimiento.year - (
        (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
    )

def _estado_control(proximo_control):
    if not proximo_control:
        return None
    delta = (proximo_control - date.today()).days
    if delta < 0:
        return "vencido"
    if delta <= 7:
        return "proximo"
    return "ok"

def make_templates(directory: str) -> Jinja2Templates:
    """Crea una instancia de Jinja2Templates con todos los filtros registrados."""
    t = Jinja2Templates(directory=directory)
    t.env.filters["calcular_edad"] = _calcular_edad
    t.env.filters["estado_control"] = _estado_control
    return t


# ── Flash messages ────────────────────────────────────────────────────────────

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


def render_template(
    templates: Jinja2Templates,
    request: Request,
    name: str,
    context: dict[str, Any] | None = None,
):
    context = context or {}
    context.setdefault("flash_messages", get_flash_messages(request))
    user_id = get_current_user_id(request)
    context.setdefault("csrf_token", create_csrf_token(user_id) if user_id else "")
    context.setdefault("current_user_is_admin", _is_admin(request))
    response = templates.TemplateResponse(request=request, name=name, context=context)
    response.delete_cookie(FLASH_COOKIE, path="/")
    return response


def check_csrf(token: str | None, request: Request) -> None:
    user_id = get_current_user_id(request)
    if not verify_csrf_token(token, user_id):
        raise HTTPException(status_code=403, detail="Token CSRF inválido.")


def set_flash_message(response: Response, message: str):
    response.set_cookie(FLASH_COOKIE, json.dumps([message]), path="/", max_age=30)
