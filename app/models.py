from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base

class Paciente(Base):
    __tablename__ = "pacientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    dni = Column(String, unique=True, index=True)
    fecha_nacimiento = Column(Date, nullable=True)
    telefono = Column(String, nullable=True)
    antecedentes = Column(Text, nullable=True)
    tipo_piel = Column(String, nullable=True)  # clara, media, oscura, etc
    alergias = Column(Text, nullable=True)
    medicaciones_actuales = Column(Text, nullable=True)

    consultas = relationship("Consulta", back_populates="paciente", cascade="all, delete-orphan")


class Consulta(Base):
    __tablename__ = "consultas"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    fecha = Column(Date, nullable=False, index=True)
    
    # Datos clínicos básicos
    motivo = Column(String, nullable=False)
    diagnostico = Column(String, nullable=True, index=True)
    
    # Datos dermatológicos específicos
    zona_afectada = Column(String, nullable=True)  # cara, brazos, piernas, espalda, etc
    tipo_lesion = Column(String, nullable=True)  # papula, placa, vesícula, etc
    duracion = Column(String, nullable=True)  # "3 días", "2 semanas", etc
    severidad = Column(String, nullable=True)  # leve, moderada, severa
    evolucion = Column(String, nullable=True)  # mejorando, estable, empeorando
    observaciones_clinicas = Column(Text, nullable=True)  # hallazgos del examen
    
    # Tratamiento y seguimiento
    tratamiento = Column(Text, nullable=True)
    recomendaciones = Column(Text, nullable=True)
    
    # Notas generales
    notas = Column(Text, nullable=True)
    # fotos_url = Column(String, nullable=True)  # para uso futuro

    paciente = relationship("Paciente", back_populates="consultas")
