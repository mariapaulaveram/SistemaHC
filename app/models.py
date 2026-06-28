from sqlalchemy import Column, Integer, String, Date
from .database import Base

class Paciente(Base):
    __tablename__ = "pacientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    dni = Column(String, unique=True, index=True)
    fecha_nacimiento = Column(Date, nullable=True)
    telefono = Column(String, nullable=True)
    antecedentes = Column(String, nullable=True)
