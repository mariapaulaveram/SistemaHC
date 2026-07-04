import os

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates  # kept for type hints
from sqlalchemy.orm import Session

from .. import models, database
from ..auth import verify_password, create_session_cookie, delete_session_cookie, get_current_user_id, verify_csrf_token
from ..utils import render_template, make_templates

router = APIRouter(tags=["auth"])
templates = make_templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))


@router.get("/login")
def login_form(request: Request, next: str = "/"):
    if get_current_user_id(request) is not None:
        return RedirectResponse(url="/", status_code=303)
    return render_template(templates, request, "login.html", {"next": next})


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: str = Form("/"),
    db: Session = Depends(database.get_db),
):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if not usuario or not verify_password(password, usuario.hashed_password):
        return render_template(
            templates, request, "login.html",
            {"error": "Email o contraseña incorrectos.", "next": next},
        )
    response = RedirectResponse(url=next if next.startswith("/") else "/", status_code=303)
    create_session_cookie(response, usuario.id, rol=usuario.rol or "medico")
    return response


@router.post("/logout")
def logout(
    request: Request,
    csrf_token: str = Form(default=""),
):
    # El logout no necesita CSRF estricto (el peor caso es cerrar sesión involuntariamente)
    # pero validamos igual como buena práctica
    user_id = get_current_user_id(request)
    if user_id and not verify_csrf_token(csrf_token, user_id):
        # Si el token es inválido simplemente redirigimos sin cerrar sesión
        return RedirectResponse(url="/", status_code=303)
    response = RedirectResponse(url="/login", status_code=303)
    delete_session_cookie(response)
    return response
