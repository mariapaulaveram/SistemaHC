from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .. import models, schemas, database
import os

router = APIRouter(prefix="/pacientes", tags=["pacientes"])
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

@router.get("")
def pagina_pacientes(request: Request, db: Session = Depends(database.get_db)):
    pacientes = db.query(models.Paciente).order_by(models.Paciente.nombre).all()
    return templates.TemplateResponse(request=request, name="lista_pacientes.html", context={"pacientes": pacientes})

@router.get("/lista")
def listar_pacientes_web(request: Request, db: Session = Depends(database.get_db)):
    pacientes = db.query(models.Paciente).order_by(models.Paciente.nombre).all()
    return templates.TemplateResponse(request=request, name="lista_pacientes_items.html", context={"pacientes": pacientes})

@router.get("/nuevo")
def pagina_crear_paciente(request: Request):
    return templates.TemplateResponse(request=request, name="crear_paciente.html")

@router.get("/{paciente_id}/editar")
def editar_paciente_form(request: Request, paciente_id: int, db: Session = Depends(database.get_db)):
    paciente = db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return templates.TemplateResponse(
        request=request,
        name="paciente_editar.html",
        context={"paciente": paciente, "error": None},
    )

@router.post("/{paciente_id}/editar")
def editar_paciente(
    request: Request,
    paciente_id: int,
    nombre: str = Form(...),
    dni: str = Form(...),
    fecha_nacimiento: str = Form(None),
    telefono: str = Form(None),
    tipo_piel: str = Form(None),
    alergias: str = Form(None),
    medicaciones_actuales: str = Form(None),
    antecedentes: str = Form(None),
    db: Session = Depends(database.get_db),
):
    paciente = db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    fecha_nacimiento_parsed = None
    if fecha_nacimiento:
        fecha_nacimiento_parsed = datetime.strptime(fecha_nacimiento, "%Y-%m-%d").date()

    paciente.nombre = nombre
    paciente.dni = dni
    paciente.fecha_nacimiento = fecha_nacimiento_parsed
    paciente.telefono = telefono
    paciente.tipo_piel = tipo_piel
    paciente.alergias = alergias
    paciente.medicaciones_actuales = medicaciones_actuales
    paciente.antecedentes = antecedentes

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse(
            request=request,
            name="paciente_editar.html",
            context={
                "paciente": paciente,
                "error": f"Ya existe un paciente con el DNI {dni}.",
            },
        )

    return RedirectResponse(url=f"/pacientes/{paciente_id}", status_code=303)

@router.get("/{paciente_id}")
def ver_paciente(request: Request, paciente_id: int, db: Session = Depends(database.get_db)):
    paciente = db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    consultas = (
        db.query(models.Consulta)
        .filter(models.Consulta.paciente_id == paciente_id)
        .order_by(models.Consulta.fecha.desc())
        .all()
    )
    return templates.TemplateResponse(
        request=request,
        name="paciente_detalle.html",
        context={"paciente": paciente, "consultas": consultas},
    )

@router.post("/")
def crear_paciente_web(
    request: Request,
    nombre: str = Form(...),
    dni: str = Form(...),
    fecha_nacimiento: str = Form(None),
    telefono: str = Form(None),
    tipo_piel: str = Form(None),
    alergias: str = Form(None),
    medicaciones_actuales: str = Form(None),
    antecedentes: str = Form(None),
    db: Session = Depends(database.get_db),
):
    fecha_nacimiento_parsed = None
    if fecha_nacimiento:
        fecha_nacimiento_parsed = datetime.strptime(fecha_nacimiento, "%Y-%m-%d").date()

    nuevo = models.Paciente(
        nombre=nombre,
        dni=dni,
        fecha_nacimiento=fecha_nacimiento_parsed,
        telefono=telefono,
        tipo_piel=tipo_piel,
        alergias=alergias,
        medicaciones_actuales=medicaciones_actuales,
        antecedentes=antecedentes,
    )
    db.add(nuevo)
    try:
        db.commit()
        db.refresh(nuevo)
        return RedirectResponse(url=f"/pacientes/{nuevo.id}", status_code=303)
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse(
            request=request,
            name="crear_paciente.html",
            context={
                "error": f"Ya existe un paciente con el DNI {dni}.",
                "form_data": {
                    "nombre": nombre,
                    "dni": dni,
                    "fecha_nacimiento": fecha_nacimiento,
                    "telefono": telefono,
                    "tipo_piel": tipo_piel,
                    "alergias": alergias,
                    "medicaciones_actuales": medicaciones_actuales,
                    "antecedentes": antecedentes,
                },
            },
        )

@router.post("/api", response_model=schemas.Paciente)
def crear_paciente_api(paciente: schemas.PacienteCreate, db: Session = Depends(database.get_db)):
    nuevo = models.Paciente(**paciente.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

