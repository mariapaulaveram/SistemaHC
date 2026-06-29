from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
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
    db.commit()
    db.refresh(nuevo)
    return RedirectResponse(url=f"/pacientes/{nuevo.id}", status_code=303)

@router.post("/api", response_model=schemas.Paciente)
def crear_paciente_api(paciente: schemas.PacienteCreate, db: Session = Depends(database.get_db)):
    nuevo = models.Paciente(**paciente.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

