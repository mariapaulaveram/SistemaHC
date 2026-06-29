from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from . import models
from .database import engine, get_db
from .routers import pacientes, consultas
import os

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
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
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"total_pacientes": total_pacientes},
    )
