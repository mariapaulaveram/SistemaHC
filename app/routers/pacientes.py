from datetime import datetime

from fastapi import APIRouter, Depends, Form, Query, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import or_, asc, desc
from .. import models, schemas, database
from ..utils import render_template, set_flash_message
import os


def parse_bool_query(value: str | None) -> bool | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"1", "true", "si", "s", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    return None

router = APIRouter(prefix="/pacientes", tags=["pacientes"])
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

@router.get("/")
def pagina_pacientes(
    request: Request,
    q: str | None = Query(None, title="Buscar"),
    tipo_piel: str | None = Query(None),
    con_antecedentes: str | None = Query(None),
    sort: str = Query("nombre", pattern="^(nombre|dni|fecha_nacimiento)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(database.get_db),
):
    query = db.query(models.Paciente)

    if q:
        q = q.strip()
        # Si el usuario buscó por DNI exacto, redirigir a la ficha del paciente
        # Esto permite desde el buscador (hero o lista) abrir directamente el paciente
        try:
            paciente_exacto = db.query(models.Paciente).filter(models.Paciente.dni == q).first()
            if paciente_exacto:
                response = RedirectResponse(url=f"/pacientes/{paciente_exacto.id}", status_code=303)
                return response
        except Exception:
            # Fallar silenciosamente y continuar con la búsqueda general
            pass
        q_pattern = f"%{q}%"
        query = query.filter(
            or_(
                models.Paciente.nombre.ilike(q_pattern),
                models.Paciente.dni.ilike(q_pattern),
            )
        )

    if tipo_piel:
        query = query.filter(models.Paciente.tipo_piel == tipo_piel)

    antecedentes_filter = parse_bool_query(con_antecedentes)
    if antecedentes_filter is not None:
        if antecedentes_filter:
            query = query.filter(models.Paciente.antecedentes != None).filter(models.Paciente.antecedentes != "")
        else:
            query = query.filter(or_(models.Paciente.antecedentes == None, models.Paciente.antecedentes == ""))

    order_col = getattr(models.Paciente, sort)
    if order == "desc":
        order_col = desc(order_col)
    else:
        order_col = asc(order_col)

    pacientes = query.order_by(order_col).all()
    return render_template(
        templates,
        request,
        "lista_pacientes.html",
        {
            "pacientes": pacientes,
            "search_params": {
                "q": q,
                "tipo_piel": tipo_piel,
                "con_antecedentes": con_antecedentes,
                "sort": sort,
                "order": order,
            },
        },
    )

@router.get("/lista")
def listar_pacientes_web(request: Request, db: Session = Depends(database.get_db)):
    pacientes = db.query(models.Paciente).order_by(models.Paciente.nombre).all()
    return templates.TemplateResponse(request=request, name="lista_pacientes_items.html", context={"pacientes": pacientes})

@router.get("/nuevo")
def pagina_crear_paciente(request: Request):
    return render_template(
        templates,
        request,
        "crear_paciente.html",
        {"form_data": {}},
    )

@router.get("/{paciente_id}/editar")
def editar_paciente_form(request: Request, paciente_id: int, db: Session = Depends(database.get_db)):
    paciente = db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return render_template(
        templates,
        request,
        "paciente_editar.html",
        {"paciente": paciente, "error": None},
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
        return render_template(
            templates,
            request,
            "paciente_editar.html",
            {
                "paciente": paciente,
                "error": f"Ya existe un paciente con el DNI {dni}.",
            },
        )

    response = RedirectResponse(url=f"/pacientes/{paciente_id}", status_code=303)
    set_flash_message(response, "Paciente actualizado correctamente.")
    return response

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
    return render_template(
        templates,
        request,
        "paciente_detalle.html",
        {"paciente": paciente, "consultas": consultas},
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
        response = RedirectResponse(url=f"/pacientes/{nuevo.id}", status_code=303)
        set_flash_message(response, "Paciente creado correctamente.")
        return response
    except IntegrityError:
        db.rollback()
        return render_template(
            templates,
            request,
            "crear_paciente.html",
            {
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

