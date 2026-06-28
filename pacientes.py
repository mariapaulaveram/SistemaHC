from datetime import date, datetime

from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .. import models, schemas, database
import os

router = APIRouter(prefix="/pacientes", tags=["pacientes"])
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))


# --- Rutas API (JSON) ---

@router.post("/api", response_model=schemas.Paciente)
def crear_paciente_api(paciente: schemas.PacienteCreate, db: Session = Depends(database.get_db)):
    nuevo_paciente = models.Paciente(**paciente.model_dump())
    db.add(nuevo_paciente)
    db.commit()
    db.refresh(nuevo_paciente)
    return nuevo_paciente


@router.get("/api", response_model=list[schemas.Paciente])
def listar_pacientes_api(db: Session = Depends(database.get_db)):
    return db.query(models.Paciente).all()


# --- Rutas WEB (paginas HTML) ---

@router.post("/")
def crear_paciente_web(
    request: Request,
    nombre: str = Form(...),
    dni: str = Form(...),
    fecha_nacimiento: str = Form(None),
    telefono: str = Form(None),
    antecedentes: str = Form(None),
    db: Session = Depends(database.get_db),
):
    fecha_nacimiento_parsed: date | None = None
    if fecha_nacimiento:
        fecha_nacimiento_parsed = datetime.strptime(fecha_nacimiento, "%Y-%m-%d").date()

    nuevo_paciente = models.Paciente(
        nombre=nombre,
        dni=dni,
        fecha_nacimiento=fecha_nacimiento_parsed,
        telefono=telefono,
        antecedentes=antecedentes,
    )
    db.add(nuevo_paciente)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse(
            request=request,
            name="paciente_form.html",
            context={
                "error": f"Ya existe un paciente con el DNI {dni}.",
                "form": {
                    "nombre": nombre,
                    "dni": dni,
                    "fecha_nacimiento": fecha_nacimiento,
                    "telefono": telefono,
                    "antecedentes": antecedentes,
                },
            },
            status_code=400,
        )
    db.refresh(nuevo_paciente)

    # Despues de crear, vamos directo a la ficha del paciente nuevo
    return RedirectResponse(url=f"/pacientes/{nuevo_paciente.id}", status_code=303)


@router.get("/lista")
def listar_pacientes_web(request: Request, q: str = "", db: Session = Depends(database.get_db)):
    query = db.query(models.Paciente)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (models.Paciente.nombre.ilike(like)) | (models.Paciente.dni.ilike(like))
        )
    pacientes = query.order_by(models.Paciente.nombre).all()
    return templates.TemplateResponse(request=request, name="lista_pacientes.html", context={"pacientes": pacientes})


@router.get("/nuevo")
def form_nuevo_paciente(request: Request):
    return templates.TemplateResponse(request=request, name="paciente_form.html", context={})


@router.get("")
def pagina_pacientes(request: Request):
    return templates.TemplateResponse(request=request, name="pacientes_lista.html", context={})


@router.get("/{paciente_id}")
def ver_paciente(request: Request, paciente_id: int, db: Session = Depends(database.get_db)):
    paciente = db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return templates.TemplateResponse(request=request, name="paciente_detalle.html", context={"paciente": paciente})
