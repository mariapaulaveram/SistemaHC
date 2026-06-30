from datetime import datetime
import logging

from fastapi import APIRouter, Depends, Form, Query, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates  # kept for type hints
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import or_, asc, desc
from .. import models, schemas, database
from ..auth import require_login
from ..utils import render_template, make_templates, set_flash_message, check_csrf
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pacientes", tags=["pacientes"], dependencies=[Depends(require_login)])
templates = make_templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))


@router.get("/")
@router.get("")
def pagina_pacientes(
    request: Request,
    q: str | None = Query(None, title="Buscar"),
    sort: str = Query("nombre", pattern="^(nombre|dni|fecha_nacimiento)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(database.get_db),
):
    query = db.query(models.Paciente).distinct()

    if q:
        q = q.strip()
        logger.info(f"BUSQUEDA: q={repr(q)}")

        paciente_exacto = db.query(models.Paciente).filter(models.Paciente.dni == q).first()
        if paciente_exacto:
            return RedirectResponse(url=f"/pacientes/{paciente_exacto.id}", status_code=303)

        q_pattern = f"%{q}%"
        query = (
            query
            .outerjoin(models.Consulta, models.Consulta.paciente_id == models.Paciente.id)
            .filter(
                or_(
                    models.Paciente.nombre.ilike(q_pattern),
                    models.Paciente.dni.ilike(q_pattern),
                    models.Consulta.diagnostico.ilike(q_pattern),
                    models.Consulta.tipo_lesion.ilike(q_pattern),
                )
            )
        )

    order_col = getattr(models.Paciente, sort)
    order_col = desc(order_col) if order == "desc" else asc(order_col)
    pacientes = query.order_by(order_col).all()

    return render_template(
        templates, request, "lista_pacientes.html",
        {"pacientes": pacientes, "search_params": {"q": q, "sort": sort, "order": order}},
    )


@router.get("/lista")
def listar_pacientes_web(
    request: Request,
    db: Session = Depends(database.get_db),
    limit: int | None = Query(None, ge=1, le=100),
    recent: bool = Query(False),
):
    query = db.query(models.Paciente)
    if recent:
        query = query.order_by(models.Paciente.id.desc())
    else:
        query = query.order_by(models.Paciente.nombre)
    if limit:
        query = query.limit(limit)
    pacientes = query.all()
    return templates.TemplateResponse(
        request=request,
        name="lista_pacientes_items.html",
        context={"pacientes": pacientes},
    )


@router.get("/nuevo")
def pagina_crear_paciente(request: Request):
    return render_template(templates, request, "crear_paciente.html", {"form_data": {}})


@router.get("/{paciente_id}/editar")
def editar_paciente_form(request: Request, paciente_id: int, db: Session = Depends(database.get_db)):
    paciente = db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return render_template(templates, request, "paciente_editar.html", {"paciente": paciente, "error": None})


@router.post("/{paciente_id}/editar")
def editar_paciente(
    request: Request,
    paciente_id: int,
    csrf_token: str = Form(default=""),
    nombre: str = Form(...),
    dni: str = Form(...),
    fecha_nacimiento: str = Form(None),
    sexo: str = Form(None),
    ocupacion: str = Form(None),
    telefono: str = Form(None),
    tipo_piel: str = Form(None),
    alergias: str = Form(None),
    medicaciones_actuales: str = Form(None),
    antecedentes: str = Form(None),
    db: Session = Depends(database.get_db),
):
    check_csrf(csrf_token, request)
    paciente = db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    paciente.nombre = nombre
    paciente.dni = dni
    paciente.fecha_nacimiento = datetime.strptime(fecha_nacimiento, "%Y-%m-%d").date() if fecha_nacimiento else None
    paciente.sexo = sexo
    paciente.ocupacion = ocupacion
    paciente.telefono = telefono
    paciente.tipo_piel = tipo_piel
    paciente.alergias = alergias
    paciente.medicaciones_actuales = medicaciones_actuales
    paciente.antecedentes = antecedentes

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return render_template(templates, request, "paciente_editar.html", {
            "paciente": paciente,
            "error": f"Ya existe un paciente con el DNI {dni}.",
        })

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
    return render_template(templates, request, "paciente_detalle.html", {"paciente": paciente, "consultas": consultas})


@router.post("/")
def crear_paciente_web(
    request: Request,
    csrf_token: str = Form(default=""),
    nombre: str = Form(...),
    dni: str = Form(...),
    fecha_nacimiento: str = Form(None),
    sexo: str = Form(None),
    ocupacion: str = Form(None),
    telefono: str = Form(None),
    tipo_piel: str = Form(None),
    alergias: str = Form(None),
    medicaciones_actuales: str = Form(None),
    antecedentes: str = Form(None),
    db: Session = Depends(database.get_db),
):
    check_csrf(csrf_token, request)
    nuevo = models.Paciente(
        nombre=nombre,
        dni=dni,
        fecha_nacimiento=datetime.strptime(fecha_nacimiento, "%Y-%m-%d").date() if fecha_nacimiento else None,
        sexo=sexo,
        ocupacion=ocupacion,
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
        return render_template(templates, request, "crear_paciente.html", {
            "error": f"Ya existe un paciente con el DNI {dni}.",
            "form_data": {
                "nombre": nombre, "dni": dni, "fecha_nacimiento": fecha_nacimiento,
                "sexo": sexo, "ocupacion": ocupacion, "telefono": telefono,
                "tipo_piel": tipo_piel, "alergias": alergias,
                "medicaciones_actuales": medicaciones_actuales, "antecedentes": antecedentes,
            },
        })


@router.get("/{paciente_id}/imprimir")
def imprimir_paciente(request: Request, paciente_id: int, db: Session = Depends(database.get_db)):
    paciente = db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    consultas = (
        db.query(models.Consulta)
        .filter(models.Consulta.paciente_id == paciente_id)
        .order_by(models.Consulta.fecha.desc())
        .all()
    )
    from datetime import date
    return render_template(templates, request, "paciente_imprimir.html", {
        "paciente": paciente,
        "consultas": consultas,
        "fecha_hoy": date.today().strftime("%d/%m/%Y"),
    })


@router.post("/api", response_model=schemas.Paciente)
def crear_paciente_api(paciente: schemas.PacienteCreate, db: Session = Depends(database.get_db)):
    nuevo = models.Paciente(**paciente.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo
