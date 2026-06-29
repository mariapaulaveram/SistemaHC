from pydantic import BaseModel
from datetime import date
from typing import Optional, List

class ConsultaBase(BaseModel):
    fecha: date
    motivo: str
    diagnostico: Optional[str] = None
    zona_afectada: Optional[str] = None
    tipo_lesion: Optional[str] = None
    duracion: Optional[str] = None
    severidad: Optional[str] = None
    evolucion: Optional[str] = None
    observaciones_clinicas: Optional[str] = None
    tratamiento: Optional[str] = None
    recomendaciones: Optional[str] = None
    notas: Optional[str] = None

class ConsultaCreate(ConsultaBase):
    pass

class Consulta(ConsultaBase):
    id: int
    paciente_id: int

    class Config:
        from_attributes = True

class PacienteBase(BaseModel):
    nombre: str
    dni: str
    fecha_nacimiento: Optional[date] = None
    telefono: Optional[str] = None
    antecedentes: Optional[str] = None
    tipo_piel: Optional[str] = None
    alergias: Optional[str] = None
    medicaciones_actuales: Optional[str] = None

class PacienteCreate(PacienteBase):
    pass

class Paciente(PacienteBase):
    id: int
    consultas: Optional[List[Consulta]] = None

    class Config:
        from_attributes = True
