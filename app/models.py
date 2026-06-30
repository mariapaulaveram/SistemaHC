from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base


class Paciente(Base):
    __tablename__ = "pacientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    dni = Column(String, unique=True, index=True)
    fecha_nacimiento = Column(Date, nullable=True)
    sexo = Column(String, nullable=True)
    ocupacion = Column(String, nullable=True)
    telefono = Column(String, nullable=True)
    antecedentes = Column(Text, nullable=True)
    tipo_piel = Column(String, nullable=True)
    alergias = Column(Text, nullable=True)
    medicaciones_actuales = Column(Text, nullable=True)

    consultas = relationship("Consulta", back_populates="paciente", cascade="all, delete-orphan")


class Consulta(Base):
    __tablename__ = "consultas"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    fecha = Column(Date, nullable=False, index=True)
    proximo_control = Column(Date, nullable=True)

    # Anamnesis
    motivo = Column(String, nullable=False)
    duracion = Column(String, nullable=True)
    sintomas = Column(Text, nullable=True)
    factores_desencadenantes = Column(Text, nullable=True)
    tratamientos_previos = Column(Text, nullable=True)

    # Examen dermatológico
    zona_afectada = Column(String, nullable=True)
    tipo_lesion = Column(String, nullable=True)
    lesion_secundaria = Column(String, nullable=True)
    severidad = Column(String, nullable=True)
    evolucion = Column(String, nullable=True)
    observaciones_clinicas = Column(Text, nullable=True)

    # Diagnóstico
    diagnostico = Column(String, nullable=True, index=True)
    diagnostico_diferencial = Column(Text, nullable=True)

    # Plan terapéutico
    estudios_solicitados = Column(Text, nullable=True)
    procedimientos = Column(Text, nullable=True)
    tratamiento = Column(Text, nullable=True)
    recomendaciones = Column(Text, nullable=True)

    # Notas internas
    notas = Column(Text, nullable=True)

    paciente = relationship("Paciente", back_populates="consultas")
    imagenes = relationship("ImagenConsulta", back_populates="consulta", cascade="all, delete-orphan")


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)


class ImagenConsulta(Base):
    __tablename__ = "imagenes_consulta"

    id = Column(Integer, primary_key=True, index=True)
    consulta_id = Column(Integer, ForeignKey("consultas.id"), nullable=False)
    filename = Column(String, nullable=False)
    descripcion = Column(String, nullable=True)

    consulta = relationship("Consulta", back_populates="imagenes")
