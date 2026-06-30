import os
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, File, Form, Request, HTTPException, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates  # kept for type hints
from sqlalchemy.orm import Session
from .. import models, schemas, database
from ..auth import require_login
from ..utils import render_template, make_templates, set_flash_message, check_csrf

router = APIRouter(prefix="/consultas", tags=["consultas"], dependencies=[Depends(require_login)])
templates = make_templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def get_uploads_dir() -> str:
    path = os.getenv("UPLOADS_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))
    os.makedirs(path, exist_ok=True)
    return path


async def _guardar_imagenes(archivos: List[UploadFile], consulta_id: int, db: Session) -> list[str]:
    warnings = []
    for archivo in archivos:
        if not archivo.filename:
            continue
        ext = os.path.splitext(archivo.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            warnings.append(f"'{archivo.filename}' ignorado: formato no permitido.")
            continue
        contenido = await archivo.read()
        if not contenido:
            continue
        if len(contenido) > MAX_FILE_SIZE:
            warnings.append(f"'{archivo.filename}' ignorado: supera 10 MB.")
            continue
        filename = f"{consulta_id}_{uuid.uuid4().hex}{ext}"
        with open(os.path.join(get_uploads_dir(), filename), "wb") as f:
            f.write(contenido)
        db.add(models.ImagenConsulta(consulta_id=consulta_id, filename=filename))
    db.commit()
    return warnings


def _parse_date(value: str | None):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


@router.post("/pacientes/{paciente_id}")
async def crear_consulta(
    paciente_id: int,
    request: Request,
    csrf_token: str = Form(default=""),
    fecha: str = Form(...),
    proximo_control: str | None = Form(None),
    motivo: str = Form(...),
    duracion: str | None = Form(None),
    sintomas: str | None = Form(None),
    factores_desencadenantes: str | None = Form(None),
    tratamientos_previos: str | None = Form(None),
    zona_afectada: str | None = Form(None),
    tipo_lesion: str | None = Form(None),
    lesion_secundaria: str | None = Form(None),
    severidad: str | None = Form(None),
    evolucion: str | None = Form(None),
    observaciones_clinicas: str | None = Form(None),
    diagnostico: str | None = Form(None),
    diagnostico_diferencial: str | None = Form(None),
    estudios_solicitados: str | None = Form(None),
    procedimientos: str | None = Form(None),
    tratamiento: str | None = Form(None),
    recomendaciones: str | None = Form(None),
    notas: str | None = Form(None),
    archivos: List[UploadFile] = File(default=[]),
    db: Session = Depends(database.get_db),
):
    check_csrf(csrf_token, request)
    paciente = db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    if not fecha or not motivo:
        return render_template(templates, request, "paciente_detalle.html", {
            "paciente": paciente,
            "consultas": db.query(models.Consulta).filter(models.Consulta.paciente_id == paciente_id).order_by(models.Consulta.fecha.desc()).all(),
            "error": "La fecha y el motivo son obligatorios.",
            "form_data": {
                "fecha": fecha, "proximo_control": proximo_control, "motivo": motivo,
                "duracion": duracion, "sintomas": sintomas,
                "factores_desencadenantes": factores_desencadenantes,
                "tratamientos_previos": tratamientos_previos,
                "zona_afectada": zona_afectada, "tipo_lesion": tipo_lesion,
                "lesion_secundaria": lesion_secundaria,
                "severidad": severidad, "evolucion": evolucion,
                "observaciones_clinicas": observaciones_clinicas,
                "diagnostico": diagnostico,
                "diagnostico_diferencial": diagnostico_diferencial,
                "estudios_solicitados": estudios_solicitados,
                "procedimientos": procedimientos, "tratamiento": tratamiento,
                "recomendaciones": recomendaciones, "notas": notas,
            },
        })

    consulta = models.Consulta(
        paciente_id=paciente_id,
        fecha=_parse_date(fecha),
        proximo_control=_parse_date(proximo_control),
        motivo=motivo, duracion=duracion,
        sintomas=sintomas,
        factores_desencadenantes=factores_desencadenantes,
        tratamientos_previos=tratamientos_previos,
        zona_afectada=zona_afectada, tipo_lesion=tipo_lesion,
        lesion_secundaria=lesion_secundaria,
        severidad=severidad, evolucion=evolucion,
        observaciones_clinicas=observaciones_clinicas,
        diagnostico=diagnostico,
        diagnostico_diferencial=diagnostico_diferencial,
        estudios_solicitados=estudios_solicitados,
        procedimientos=procedimientos,
        tratamiento=tratamiento, recomendaciones=recomendaciones, notas=notas,
    )
    db.add(consulta)
    db.commit()
    db.refresh(consulta)

    warnings = await _guardar_imagenes(archivos, consulta.id, db)

    response = RedirectResponse(url=f"/pacientes/{paciente_id}", status_code=303)
    msg = "Consulta agregada correctamente."
    if warnings:
        msg += " Advertencias: " + " ".join(warnings)
    set_flash_message(response, msg)
    return response


@router.get("/{consulta_id}/editar")
def editar_consulta_form(consulta_id: int, request: Request, db: Session = Depends(database.get_db)):
    consulta = db.query(models.Consulta).filter(models.Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")
    return render_template(templates, request, "consulta_editar.html", {"consulta": consulta})


@router.get("/{consulta_id}")
def ver_consulta(consulta_id: int, request: Request, db: Session = Depends(database.get_db)):
    consulta = db.query(models.Consulta).filter(models.Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")
    return render_template(templates, request, "consulta_detalle.html", {"consulta": consulta})


@router.post("/{consulta_id}/editar")
def editar_consulta(
    consulta_id: int,
    request: Request,
    csrf_token: str = Form(default=""),
    fecha: str = Form(...),
    proximo_control: str | None = Form(None),
    motivo: str = Form(...),
    duracion: str | None = Form(None),
    sintomas: str | None = Form(None),
    factores_desencadenantes: str | None = Form(None),
    tratamientos_previos: str | None = Form(None),
    zona_afectada: str | None = Form(None),
    tipo_lesion: str | None = Form(None),
    lesion_secundaria: str | None = Form(None),
    severidad: str | None = Form(None),
    evolucion: str | None = Form(None),
    observaciones_clinicas: str | None = Form(None),
    diagnostico: str | None = Form(None),
    diagnostico_diferencial: str | None = Form(None),
    estudios_solicitados: str | None = Form(None),
    procedimientos: str | None = Form(None),
    tratamiento: str | None = Form(None),
    recomendaciones: str | None = Form(None),
    notas: str | None = Form(None),
    db: Session = Depends(database.get_db),
):
    check_csrf(csrf_token, request)
    consulta = db.query(models.Consulta).filter(models.Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")

    if not fecha or not motivo:
        return render_template(templates, request, "consulta_editar.html", {
            "consulta": consulta,
            "error": "La fecha y el motivo son obligatorios.",
        })

    consulta.fecha = _parse_date(fecha)
    consulta.proximo_control = _parse_date(proximo_control)
    consulta.motivo = motivo
    consulta.duracion = duracion
    consulta.sintomas = sintomas
    consulta.factores_desencadenantes = factores_desencadenantes
    consulta.tratamientos_previos = tratamientos_previos
    consulta.zona_afectada = zona_afectada
    consulta.tipo_lesion = tipo_lesion
    consulta.lesion_secundaria = lesion_secundaria
    consulta.severidad = severidad
    consulta.evolucion = evolucion
    consulta.observaciones_clinicas = observaciones_clinicas
    consulta.diagnostico = diagnostico
    consulta.diagnostico_diferencial = diagnostico_diferencial
    consulta.estudios_solicitados = estudios_solicitados
    consulta.procedimientos = procedimientos
    consulta.tratamiento = tratamiento
    consulta.recomendaciones = recomendaciones
    consulta.notas = notas
    db.commit()

    response = RedirectResponse(url=f"/pacientes/{consulta.paciente_id}", status_code=303)
    set_flash_message(response, "Consulta actualizada correctamente.")
    return response
