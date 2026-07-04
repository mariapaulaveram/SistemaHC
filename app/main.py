import os
import calendar
from datetime import date, timedelta
from collections import defaultdict

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates  # kept for type hints
from sqlalchemy.orm import Session
from sqlalchemy import func

from . import models
from .auth import require_login, get_current_user_id, LoginRequired, DemoRestricted
from .database import engine, get_db
from .routers import pacientes, consultas, imagenes, admin, perfil
from .routers import auth as auth_router
from .utils import render_template, make_templates


DIAS_ES   = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]
MESES_ES  = ["enero","febrero","marzo","abril","mayo","junio",
             "julio","agosto","septiembre","octubre","noviembre","diciembre"]
DIAS_CORTO = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]

def fecha_es(d):
    return f"{DIAS_ES[d.weekday()]} {d.day} de {MESES_ES[d.month-1]} de {d.year}"

models.Base.metadata.create_all(bind=engine)

app = FastAPI(redirect_slashes=False)


@app.on_event("startup")
def crear_admin_inicial():
    """Si ADMIN_EMAIL y ADMIN_PASSWORD están definidos y no hay usuarios, crea el admin."""
    from .auth import hash_password
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_email or not admin_password:
        return
    from .database import SessionLocal
    db = SessionLocal()
    try:
        if db.query(models.Usuario).count() == 0:
            usuario = models.Usuario(
                email=admin_email,
                hashed_password=hash_password(admin_password),
                rol="admin",
            )
            db.add(usuario)
            db.commit()
            print(f"[startup] Usuario admin creado: {admin_email}")
    finally:
        db.close()
templates = make_templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")),
    name="static",
)

UPLOADS_DIR = os.getenv("UPLOADS_DIR", os.path.join(os.path.dirname(__file__), "..", "uploads"))
os.makedirs(UPLOADS_DIR, exist_ok=True)
# /uploads protegido — requiere login
# (ya no se monta como StaticFiles público)


@app.get("/uploads/{filename}", dependencies=[Depends(require_login)])
def servir_upload(filename: str):
    """Sirve archivos de uploads solo a usuarios autenticados."""
    # Sanitizar: evitar path traversal
    filename = os.path.basename(filename)
    filepath = os.path.join(UPLOADS_DIR, filename)
    if not os.path.isfile(filepath):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(filepath)

app.include_router(auth_router.router)
app.include_router(pacientes.router)
app.include_router(consultas.router)
app.include_router(imagenes.router)
app.include_router(admin.router)
app.include_router(perfil.router)


@app.exception_handler(LoginRequired)
async def login_required_handler(request: Request, exc: LoginRequired):
    return RedirectResponse(url="/login", status_code=303)


@app.exception_handler(DemoRestricted)
async def demo_restricted_handler(request: Request, exc: DemoRestricted):
    from .utils import set_flash_message
    response = RedirectResponse(url=request.headers.get("referer", "/"), status_code=303)
    set_flash_message(response, "⚠️ Cuenta demo — solo lectura. No se pueden realizar cambios.")
    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    return templates.TemplateResponse("500.html", {"request": request}, status_code=exc.status_code)

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return templates.TemplateResponse("500.html", {"request": request}, status_code=500)


@app.get("/")
def home(request: Request, db: Session = Depends(get_db), user_id: int = Depends(require_login)):
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

    usuario = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    usuario_nombre = (usuario.nombre or usuario.email.split("@")[0]) if usuario else ""

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
            "usuario_nombre": usuario_nombre,
        },
    )


@app.get("/calendario")
def calendario(
    request: Request,
    mes: int | None = None,
    anio: int | None = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_login),
):
    hoy = date.today()
    mes  = mes  or hoy.month
    anio = anio or hoy.year

    # Navegación mes anterior / siguiente
    if mes == 1:
        mes_ant, anio_ant = 12, anio - 1
    else:
        mes_ant, anio_ant = mes - 1, anio
    if mes == 12:
        mes_sig, anio_sig = 1, anio + 1
    else:
        mes_sig, anio_sig = mes + 1, anio

    # Semanas del mes (lunes primero)
    cal = calendar.Calendar(firstweekday=0)
    semanas = cal.monthdatescalendar(anio, mes)

    # Controles del mes
    primer_dia = date(anio, mes, 1)
    ultimo_dia = date(anio, mes, calendar.monthrange(anio, mes)[1])
    controles = (
        db.query(models.Consulta)
        .filter(
            models.Consulta.proximo_control >= primer_dia,
            models.Consulta.proximo_control <= ultimo_dia,
        )
        .order_by(models.Consulta.proximo_control)
        .all()
    )

    # Índice fecha → lista de controles
    por_dia = defaultdict(list)
    for c in controles:
        por_dia[c.proximo_control].append(c)

    return render_template(
        templates, request, "calendario.html",
        {
            "hoy": hoy,
            "mes": mes,
            "anio": anio,
            "mes_nombre": MESES_ES[mes - 1].capitalize(),
            "dias_corto": DIAS_CORTO,
            "semanas": semanas,
            "por_dia": dict(por_dia),
            "mes_ant": mes_ant, "anio_ant": anio_ant,
            "mes_sig": mes_sig, "anio_sig": anio_sig,
            "total_controles": len(controles),
        },
    )
