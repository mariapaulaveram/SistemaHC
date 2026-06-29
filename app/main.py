from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from . import models
from .database import engine, get_db
from .routers import pacientes, consultas
from .utils import render_template
import os

models.Base.metadata.create_all(bind=engine)

app = FastAPI(redirect_slashes=False)  # No redirigir automáticamente /pacientes a /pacientes/
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")),
    name="static",
)

app.include_router(pacientes.router)
app.include_router(consultas.router)


@app.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    total_pacientes = db.query(models.Paciente).count()
    total_consultas = db.query(models.Consulta).count()
    recientes_pacientes = (
        db.query(models.Paciente)
        .order_by(models.Paciente.id.desc())
        .limit(5)
        .all()
    )
    return render_template(
        templates,
        request,
        "index.html",
        {
            "total_pacientes": total_pacientes,
            "total_consultas": total_consultas,
            "recientes_pacientes": recientes_pacientes,
        },
    )
