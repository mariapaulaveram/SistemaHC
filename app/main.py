from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from . import models
from .database import engine
from .routers import pacientes
import os  # <--- TIENE QUE ESTAR AQUÍ TAMBIÉN

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(pacientes.router)

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")
