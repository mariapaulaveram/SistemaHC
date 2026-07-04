import os

import bcrypt
from fastapi import Cookie, Request, HTTPException
from fastapi.responses import RedirectResponse
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

SESSION_COOKIE = "hc_session"
SESSION_MAX_AGE = 60 * 60 * 8  # 8 horas
CSRF_MAX_AGE   = 60 * 60 * 1  # 1 hora

def _get_serializer(salt: str) -> URLSafeTimedSerializer:
    secret = os.getenv("SECRET_KEY")
    if not secret:
        raise RuntimeError("SECRET_KEY no está definida en las variables de entorno.")
    return URLSafeTimedSerializer(secret, salt=salt)


# ── Contraseñas ──────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── Cookie de sesión ─────────────────────────────────────────────────────────

def create_session_cookie(response, usuario_id: int, rol: str = "medico") -> None:
    token = _get_serializer("session").dumps({"id": usuario_id, "rol": rol})
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
    )


def _decode_session(request: Request) -> dict | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    try:
        return _get_serializer("session").loads(token, max_age=SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None


def get_current_user_id(request: Request) -> int | None:
    data = _decode_session(request)
    return data.get("id") if data else None


def get_current_user_rol(request: Request) -> str | None:
    data = _decode_session(request)
    return data.get("rol") if data else None


def is_admin(request: Request) -> bool:
    return get_current_user_rol(request) == "admin"


def delete_session_cookie(response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")


# ── CSRF ─────────────────────────────────────────────────────────────────────

def create_csrf_token(user_id: int) -> str:
    return _get_serializer("csrf").dumps(user_id)


def verify_csrf_token(token: str | None, user_id: int | None) -> bool:
    if not token or not user_id:
        return False
    try:
        data = _get_serializer("csrf").loads(token, max_age=CSRF_MAX_AGE)
        return data == user_id
    except Exception:
        return False


# ── Dependencies para proteger rutas ─────────────────────────────────────────

def require_login(request: Request):
    user_id = get_current_user_id(request)
    if user_id is None:
        next_url = str(request.url)
        return RedirectResponse(url=f"/login?next={next_url}", status_code=303)
    return user_id


def require_admin(request: Request):
    user_id = get_current_user_id(request)
    if user_id is None:
        return RedirectResponse(url="/login", status_code=303)
    if not is_admin(request):
        raise HTTPException(status_code=403, detail="Acceso restringido a administradores.")
    return user_id
