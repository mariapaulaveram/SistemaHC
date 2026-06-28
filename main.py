from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from . import models
from .database import engine
from .routers import pacientes
import os

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")),
    name="static",
)

app.include_router(pacientes.router)


@app.get("/")
def home():
    return RedirectResponse(url="/pacientes")
