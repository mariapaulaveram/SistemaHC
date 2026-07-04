import os

from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models, database
from ..auth import require_admin, get_current_user_id, hash_password
from ..utils import render_template, make_templates, check_csrf

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])
templates = make_templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))


@router.get("/usuarios")
def listar_usuarios(request: Request, db: Session = Depends(database.get_db)):
    usuarios = db.query(models.Usuario).order_by(models.Usuario.id).all()
    return render_template(templates, request, "admin_usuarios.html", {
        "usuarios": usuarios,
        "current_user_id": get_current_user_id(request),
    })


@router.post("/usuarios/crear")
def crear_usuario(
    request: Request,
    csrf_token: str = Form(default=""),
    nombre: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    rol: str = Form(default="medico"),
    db: Session = Depends(database.get_db),
):
    check_csrf(csrf_token, request)
    if rol not in ("admin", "medico"):
        rol = "medico"
    existente = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if existente:
        usuarios = db.query(models.Usuario).order_by(models.Usuario.id).all()
        return render_template(templates, request, "admin_usuarios.html", {
            "usuarios": usuarios,
            "error": f"Ya existe un usuario con el email {email}.",
        })
    nuevo = models.Usuario(
        nombre=nombre.strip(),
        email=email.strip().lower(),
        hashed_password=hash_password(password),
        rol=rol,
    )
    db.add(nuevo)
    db.commit()
    return RedirectResponse(url="/admin/usuarios", status_code=303)


@router.post("/usuarios/{usuario_id}/eliminar")
def eliminar_usuario(
    request: Request,
    usuario_id: int,
    csrf_token: str = Form(default=""),
    db: Session = Depends(database.get_db),
):
    check_csrf(csrf_token, request)
    mi_id = get_current_user_id(request)
    if usuario_id == mi_id:
        raise HTTPException(status_code=400, detail="No podés eliminar tu propia cuenta.")
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404)
    db.delete(usuario)
    db.commit()
    return RedirectResponse(url="/admin/usuarios", status_code=303)


@router.post("/usuarios/{usuario_id}/cambiar-rol")
def cambiar_rol(
    request: Request,
    usuario_id: int,
    csrf_token: str = Form(default=""),
    rol: str = Form(...),
    db: Session = Depends(database.get_db),
):
    check_csrf(csrf_token, request)
    mi_id = get_current_user_id(request)
    if usuario_id == mi_id:
        raise HTTPException(status_code=400, detail="No podés cambiar tu propio rol.")
    if rol not in ("admin", "medico"):
        raise HTTPException(status_code=400)
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404)
    usuario.rol = rol
    db.commit()
    return RedirectResponse(url="/admin/usuarios", status_code=303)
