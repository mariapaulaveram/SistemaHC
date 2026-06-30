import os
from datetime import date, timedelta

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates  # kept for type hints
from sqlalchemy.orm import Session
from sqlalchemy import func

from . import models
from .auth import require_login
from .database import engine, get_db
from .routers import pacientes, consultas, imagenes
from .routers import auth as auth_router
from .utils import render_template, make_templates


DIAS_ES   = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]
MESES_ES  = ["enero","febrero","marzo","abril","mayo","junio",
             "julio","agosto","septiembre","octubre","noviembre","diciembre"]

def fecha_es(d):
    return f"{DIAS_ES[d.weekday()]} {d.day} de {MESES_ES[d.month-1]} de {d.year}"

models.Base.metadata.create_all(bind=engine)

app = FastAPI(redirect_slashes=False)
templates = make_templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")),
    name="static",
)

UPLOADS_DIR = os.getenv("UPLOADS_DIR", os.path.join(os.path.dirname(__file__), "..", "uploads"))
os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

app.include_router(auth_router.router)
app.include_router(pacientes.router)
app.include_router(consultas.router)
app.include_router(imagenes.router)


@app.get("/")
def home(request: Request, db: Session = Depends(get_db), _: int = Depends(require_login)):
    hoy = date.today()
    en_7_dias = hoy + timedelta(days=7)

    total_pacientes = db.query(models.Paciente).count()

    consultas_este_mes = db.query(models.Consulta).filter(
        func.extract("month", models.Consulta.fecha) == hoy.month,
        func.extract("year",  models.Consulta.fecha) == hoy.year,
    ).count()

    # Controles vencidos: próximo_control < hoy
    controles_vencidos = (
        db.query(models.Consulta)
        .filter(models.Consulta.proximo_control < hoy)
        .order_by(models.Consulta.proximo_control.asc())
        .limit(10)
        .all()
    )

    # Controles próximos: entre hoy y 7 días
    controles_proximos = (
        db.query(models.Consulta)
        .filter(
            models.Consulta.proximo_control >= hoy,
            models.Consulta.proximo_control <= en_7_dias,
        )
        .order_by(models.Consulta.proximo_control.asc())
        .limit(10)
        .all()
    )

    pacientes_recientes = (
        db.query(models.Paciente)
        .order_by(models.Paciente.id.desc())
        .limit(5)
        .all()
    )

    return render_template(
        templates, request, "index.html",
        {
            "hoy": hoy,
            "hoy_str": fecha_es(hoy),
            "total_pacientes": total_pacientes,
            "consultas_este_mes": consultas_este_mes,
            "controles_vencidos": controles_vencidos,
            "controles_proximos": controles_proximos,
            "pacientes_recientes": pacientes_recientes,
        },
    )
