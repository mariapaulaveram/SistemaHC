from pydantic import BaseModel
from datetime import date
from typing import Optional

class PacienteBase(BaseModel):
    nombre: str
    dni: str
    fecha_nacimiento: Optional[date] = None
    telefono: Optional[str] = None
    antecedentes: Optional[str] = None

class PacienteCreate(PacienteBase):
    pass

class Paciente(PacienteBase):
    id: int

    class Config:
        from_attributes = True
        