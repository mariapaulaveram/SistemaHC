import os

from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models, database
from ..auth import require_login, get_current_user_id, verify_password, hash_password
from ..utils import render_template, make_templates, check_csrf

router = APIRouter(prefix="/perfil", tags=["perfil"], dependencies=[Depends(require_login)])
templates = make_templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))


@router.get("")
def ver_perfil(request: Request, db: Session = Depends(database.get_db)):
    user_id = get_current_user_id(request)
    usuario = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    if not usuario:
        raise HTTPException(status_code=404)
    return render_template(templates, request, "perfil.html", {"usuario": usuario})


@router.post("/nombre")
def actualizar_nombre(
    request: Request,
    csrf_token: str = Form(default=""),
    nombre: str = Form(...),
    db: Session = Depends(database.get_db),
):
    check_csrf(csrf_token, request)
    user_id = get_current_user_id(request)
    usuario = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    if not usuario:
        raise HTTPException(status_code=404)
    usuario.nombre = nombre.strip()
    db.commit()
    return RedirectResponse(url="/perfil?ok=nombre", status_code=303)


@router.post("/password")
def cambiar_password(
    request: Request,
    csrf_token: str = Form(default=""),
    password_actual: str = Form(...),
    password_nuevo: str = Form(...),
    password_confirmar: str = Form(...),
    db: Session = Depends(database.get_db),
):
    check_csrf(csrf_token, request)
    user_id = get_current_user_id(request)
    usuario = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    if not usuario:
        raise HTTPException(status_code=404)

    if not verify_password(password_actual, usuario.hashed_password):
        return render_template(templates, request, "perfil.html", {
            "usuario": usuario,
            "error_password": "La contraseña actual es incorrecta.",
        })
    if len(password_nuevo) < 8:
        return render_template(templates, request, "perfil.html", {
            "usuario": usuario,
            "error_password": "La nueva contraseña debe tener al menos 8 caracteres.",
        })
    if password_nuevo != password_confirmar:
        return render_template(templates, request, "perfil.html", {
            "usuario": usuario,
            "error_password": "Las contraseñas nuevas no coinciden.",
        })

    usuario.hashed_password = hash_password(password_nuevo)
    db.commit()
    return RedirectResponse(url="/perfil?ok=password", status_code=303)
