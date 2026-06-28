from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .. import models, schemas, database
import os

router = APIRouter(prefix="/pacientes", tags=["pacientes"])
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

# --- RUTAS ESPECÍFICAS (DEBEN IR PRIMERO) ---

@router.get("/nuevo")
def pagina_crear_paciente(request: Request):
    return templates.TemplateResponse(request=request, name="crear_paciente.html")

@router.get("/lista")
def listar_pacientes_web(request: Request, db: Session = Depends(database.get_db)):
    pacientes = db.query(models.Paciente).all()
    return templates.TemplateResponse(request=request, name="lista_pacientes.html", context={"pacientes": pacientes})

# --- RUTA DINÁMICA (DEBE IR AL FINAL DE LAS DE TIPO GET) ---

@router.get("/{paciente_id}")
def ver_paciente(request: Request, paciente_id: int, db: Session = Depends(database.get_db)):
    paciente = db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return templates.TemplateResponse(request=request, name="paciente_detalle.html", context={"paciente": paciente})

# --- RUTAS POST / API ---

@router.post("/")
def crear_paciente_web(request: Request, nombre: str = Form(...), dni: str = Form(...), db: Session = Depends(database.get_db)):
    nuevo = models.Paciente(nombre=nombre, dni=dni)
    db.add(nuevo)
    db.commit()
    return templates.TemplateResponse(request=request, name="paciente_item.html", context={"paciente": nuevo})

@router.post("/api", response_model=schemas.Paciente)
def crear_paciente_api(paciente: schemas.PacienteCreate, db: Session = Depends(database.get_db)):
    nuevo = models.Paciente(**paciente.model_dump())
    db.add(nuevo)
    db.commit()
    return nuevo

@router.get("/", response_model=list[schemas.Paciente])
def listar_pacientes(db: Session = Depends(database.get_db)):
    return db.query(models.Paciente).all()

