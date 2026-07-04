import os
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models, database
from ..auth import require_login, require_not_demo
from ..utils import set_flash_message, check_csrf

router = APIRouter(tags=["imagenes"], dependencies=[Depends(require_login), Depends(require_not_demo)])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def get_uploads_dir() -> str:
    path = os.getenv("UPLOADS_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))
    os.makedirs(path, exist_ok=True)
    return path


@router.post("/consultas/{consulta_id}/imagenes")
async def subir_imagen(
    consulta_id: int,
    request: Request,
    csrf_token: str = Form(default=""),
    descripcion: str | None = Form(None),
    archivo: UploadFile = File(...),
    db: Session = Depends(database.get_db),
):
    check_csrf(csrf_token, request)
    consulta = db.query(models.Consulta).filter(models.Consulta.id == consulta_id).first()
    if not consulta:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")

    # Validar extensión
    ext = os.path.splitext(archivo.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        response = RedirectResponse(url=f"/consultas/{consulta_id}", status_code=303)
        set_flash_message(response, f"Formato no permitido. Usá JPG, PNG o WebP.")
        return response

    # Validar tamaño leyendo el contenido
    contenido = await archivo.read()
    if len(contenido) > MAX_FILE_SIZE:
        response = RedirectResponse(url=f"/consultas/{consulta_id}", status_code=303)
        set_flash_message(response, "La imagen supera el límite de 10 MB.")
        return response

    # Guardar con nombre único para evitar colisiones
    filename = f"{consulta_id}_{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(get_uploads_dir(), filename)
    with open(filepath, "wb") as f:
        f.write(contenido)

    imagen = models.ImagenConsulta(
        consulta_id=consulta_id,
        filename=filename,
        descripcion=descripcion or None,
    )
    db.add(imagen)
    db.commit()

    response = RedirectResponse(url=f"/consultas/{consulta_id}", status_code=303)
    set_flash_message(response, "Imagen subida correctamente.")
    return response


@router.post("/imagenes/{imagen_id}/eliminar")
def eliminar_imagen(
    imagen_id: int,
    request: Request,
    csrf_token: str = Form(default=""),
    db: Session = Depends(database.get_db),
):
    check_csrf(csrf_token, request)
    imagen = db.query(models.ImagenConsulta).filter(models.ImagenConsulta.id == imagen_id).first()
    if not imagen:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")

    consulta_id = imagen.consulta_id

    # Eliminar el archivo del disco
    filepath = os.path.join(get_uploads_dir(), imagen.filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    db.delete(imagen)
    db.commit()

    response = RedirectResponse(url=f"/consultas/{consulta_id}", status_code=303)
    set_flash_message(response, "Imagen eliminada.")
    return response
