from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .. import models, schemas, database
from ..utils import render_template, set_flash_message
import os

router = APIRouter(prefix="/consultas", tags=["consultas"])
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

@router.post("/pacientes/{paciente_id}")
def crear_consulta(
    paciente_id: int,
    request: Request,
    fecha: str = Form(...),
    motivo: str = Form(...),
    diagnostico: str | None = Form(None),
    zona_afectada: str | None = Form(None),
    tipo_lesion: str | None = Form(None),
    duracion: str | None = Form(None),
    severidad: str | None = Form(None),
    evolucion: str | None = Form(None),
    observaciones_clinicas: str | None = Form(None),
    tratamiento: str | None = Form(None),
    recomendaciones: str | None = Form(None),
    notas: str | None = Form(None),
    db: Session = Depends(database.get_db),
):
    paciente = db.query(models.Paciente).filter(models.Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    if not fecha or not motivo:
        return render_template(
            templates,
            request,
            "paciente_detalle.html",
            {
                "paciente": paciente,
                "consultas": db.query(models.Consulta).filter(models.Consulta.paciente_id == paciente_id).order_by(models.Consulta.fecha.desc()).all(),
                "error": "La fecha y el motivo son obligatorios para crear una consulta.",
                "form_data": {
                    "fecha": fecha,
                    "motivo": motivo,
                    "diagnostico": diagnostico,
                    "zona_afectada": zona_afectada,
                    "tipo_lesion": tipo_lesion,
                    "duracion": duracion,
                    "severidad": severidad,
                    "evolucion": evolucion,
                    "observaciones_clinicas": observaciones_clinicas,
                    "tratamiento": tratamiento,
                    "recomendaciones": recomendaciones,
                    "notas": notas,
                },
            },
        )

    fecha_parsed = datetime.strptime(fecha, "%Y-%m-%d").date()
    consulta = models.Consulta(
        paciente_id=paciente_id,
        fecha=fecha_parsed,
        motivo=motivo,
        diagnostico=diagnostico,
        zona_afectada=zona_afectada,
        tipo_lesion=tipo_lesion,
        duracion=duracion,
        severidad=severidad,
        evolucion=evolucion,
        observaciones_clinicas=observaciones_clinicas,
        tratamiento=tratamiento,
        recomendaciones=recomendaciones,
        notas=notas,
    )
    db.add(consulta)
    db.commit()
    db.refresh(consulta)
    response = RedirectResponse(url=f"/pacientes/{paciente_id}", status_code=303)
    set_flash_message(response, "Consulta agregada correctamente.")
    return response

@router.get("/{consulta_id}/editar")
def editar_consulta_form(consulta_id: int, request: Request, db: Session = Depends(database.get_db)):
    consulta = db.query(models.Consulta).filter(models.Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")
    return render_template(
        templates,
        request,
        "consulta_editar.html",
        {"consulta": consulta},
    )


@router.get("/{consulta_id}")
def ver_consulta(consulta_id: int, request: Request, db: Session = Depends(database.get_db)):
    consulta = db.query(models.Consulta).filter(models.Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")
    return render_template(
        templates,
        request,
        "consulta_detalle.html",
        {"consulta": consulta},
    )

@router.post("/{consulta_id}/editar")
def editar_consulta(
    consulta_id: int,
    request: Request,
    fecha: str = Form(...),
    motivo: str = Form(...),
    diagnostico: str | None = Form(None),
    zona_afectada: str | None = Form(None),
    tipo_lesion: str | None = Form(None),
    duracion: str | None = Form(None),
    severidad: str | None = Form(None),
    evolucion: str | None = Form(None),
    observaciones_clinicas: str | None = Form(None),
    tratamiento: str | None = Form(None),
    recomendaciones: str | None = Form(None),
    notas: str | None = Form(None),
    db: Session = Depends(database.get_db),
):
    consulta = db.query(models.Consulta).filter(models.Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")

    if not fecha or not motivo:
        return render_template(
            templates,
            request,
            "consulta_editar.html",
            {
                "consulta": consulta,
                "error": "La fecha y el motivo son obligatorios para editar la consulta.",
                "form_data": {
                    "fecha": fecha,
                    "motivo": motivo,
                    "diagnostico": diagnostico,
                    "zona_afectada": zona_afectada,
                    "tipo_lesion": tipo_lesion,
                    "duracion": duracion,
                    "severidad": severidad,
                    "evolucion": evolucion,
                    "observaciones_clinicas": observaciones_clinicas,
                    "tratamiento": tratamiento,
                    "recomendaciones": recomendaciones,
                    "notas": notas,
                },
            },
        )

    consulta.fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
    consulta.motivo = motivo
    consulta.diagnostico = diagnostico
    consulta.zona_afectada = zona_afectada
    consulta.tipo_lesion = tipo_lesion
    consulta.duracion = duracion
    consulta.severidad = severidad
    consulta.evolucion = evolucion
    consulta.observaciones_clinicas = observaciones_clinicas
    consulta.tratamiento = tratamiento
    consulta.recomendaciones = recomendaciones
    consulta.notas = notas
    db.commit()
    response = RedirectResponse(url=f"/pacientes/{consulta.paciente_id}", status_code=303)
    set_flash_message(response, "Consulta actualizada correctamente.")
    return response
