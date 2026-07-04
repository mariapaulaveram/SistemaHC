import os
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models, database
from ..auth import require_admin, get_current_user_id, hash_password
from ..utils import render_template, make_templates, check_csrf, set_flash_message

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])
templates = make_templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))


@router.get("/usuarios")
def listar_usuarios(request: Request, db: Session = Depends(database.get_db)):
    usuarios = db.query(models.Usuario).order_by(models.Usuario.id).all()
    return render_template(templates, request, "admin_usuarios.html", {
        "usuarios": usuarios,
        "current_user_id": get_current_user_id(request),
    })


@router.post("/usuarios/crear")
def crear_usuario(
    request: Request,
    csrf_token: str = Form(default=""),
    nombre: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    rol: str = Form(default="medico"),
    db: Session = Depends(database.get_db),
):
    check_csrf(csrf_token, request)
    if rol not in ("admin", "medico", "demo"):
        rol = "medico"
    existente = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if existente:
        usuarios = db.query(models.Usuario).order_by(models.Usuario.id).all()
        return render_template(templates, request, "admin_usuarios.html", {
            "usuarios": usuarios,
            "error": f"Ya existe un usuario con el email {email}.",
        })
    nuevo = models.Usuario(
        nombre=nombre.strip(),
        email=email.strip().lower(),
        hashed_password=hash_password(password),
        rol=rol,
    )
    db.add(nuevo)
    db.commit()
    return RedirectResponse(url="/admin/usuarios", status_code=303)


@router.post("/usuarios/{usuario_id}/eliminar")
def eliminar_usuario(
    request: Request,
    usuario_id: int,
    csrf_token: str = Form(default=""),
    db: Session = Depends(database.get_db),
):
    check_csrf(csrf_token, request)
    mi_id = get_current_user_id(request)
    if usuario_id == mi_id:
        raise HTTPException(status_code=400, detail="No podés eliminar tu propia cuenta.")
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404)
    db.delete(usuario)
    db.commit()
    return RedirectResponse(url="/admin/usuarios", status_code=303)


@router.post("/usuarios/{usuario_id}/cambiar-rol")
def cambiar_rol(
    request: Request,
    usuario_id: int,
    csrf_token: str = Form(default=""),
    rol: str = Form(...),
    db: Session = Depends(database.get_db),
):
    check_csrf(csrf_token, request)
    mi_id = get_current_user_id(request)
    if usuario_id == mi_id:
        raise HTTPException(status_code=400, detail="No podés cambiar tu propio rol.")
    if rol not in ("admin", "medico", "demo"):
        raise HTTPException(status_code=400)
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404)
    usuario.rol = rol
    db.commit()
    return RedirectResponse(url="/admin/usuarios", status_code=303)


@router.post("/fix-fechas-demo")
def fix_fechas_demo(
    request: Request,
    csrf_token: str = Form(default=""),
    db: Session = Depends(database.get_db),
):
    """Actualiza las fechas de las primeras 3 consultas al mes actual para el dashboard."""
    check_csrf(csrf_token, request)
    hoy = date.today()
    consultas = db.query(models.Consulta).order_by(models.Consulta.fecha.asc()).limit(5).all()
    nuevas_fechas = [hoy, hoy - timedelta(days=1), hoy - timedelta(days=2),
                     hoy - timedelta(days=3), hoy - timedelta(days=4)]
    for i, consulta in enumerate(consultas):
        consulta.fecha = nuevas_fechas[i]
    db.commit()
    response = RedirectResponse(url="/", status_code=303)
    set_flash_message(response, f"✓ Fechas de {len(consultas)} consultas actualizadas al mes actual.")
    return response


@router.post("/seed-demo")
def seed_demo(
    request: Request,
    csrf_token: str = Form(default=""),
    db: Session = Depends(database.get_db),
):
    """Carga pacientes de demo. Solo funciona si hay menos de 3 pacientes."""
    check_csrf(csrf_token, request)
    if db.query(models.Paciente).count() >= 3:
        response = RedirectResponse(url="/admin/usuarios", status_code=303)
        set_flash_message(response, "Ya hay pacientes cargados. Seed cancelado.")
        return response

    hoy = date.today()
    medico_id = get_current_user_id(request)

    PACIENTES = [
        dict(nombre="Ana García López", dni="28451236", fecha_nacimiento=date(1985, 3, 12),
             sexo="Femenino", ocupacion="Docente", telefono="1154321098",
             tipo_piel="Tipo II (piel clara, pelo castaño)", alergias="Penicilina",
             medicaciones_actuales="Anticonceptivos orales",
             antecedentes="Rinitis alérgica. Sin antecedentes dermatológicos relevantes."),
        dict(nombre="Carlos Méndez Ruiz", dni="35672891", fecha_nacimiento=date(1990, 7, 28),
             sexo="Masculino", ocupacion="Programador", telefono="1167894523",
             tipo_piel="Tipo III (piel intermedia, broncea gradualmente)",
             alergias="Ninguna conocida", medicaciones_actuales="Ninguna",
             antecedentes="Psoriasis en placas diagnosticada en 2019."),
        dict(nombre="Laura Fernández Costa", dni="22198745", fecha_nacimiento=date(1978, 11, 5),
             sexo="Femenino", ocupacion="Enfermera", telefono="1143219876",
             tipo_piel="Tipo I (piel muy clara, siempre se quema)", alergias="Látex, ibuprofeno",
             medicaciones_actuales="Levotiroxina 50mcg",
             antecedentes="Hipotiroidismo. Dermatitis atópica desde la infancia."),
        dict(nombre="Roberto Sosa Villalba", dni="31045678", fecha_nacimiento=date(1968, 4, 20),
             sexo="Masculino", ocupacion="Contador", telefono="1198765432",
             tipo_piel="Tipo IV (piel morena clara, raramente se quema)",
             alergias="Ninguna", medicaciones_actuales="Enalapril 10mg, Metformina 850mg",
             antecedentes="Diabetes tipo 2, HTA. Consulta previa por queratosis actínica."),
        dict(nombre="Valentina Torres Díaz", dni="40123456", fecha_nacimiento=date(2001, 9, 15),
             sexo="Femenino", ocupacion="Estudiante universitaria", telefono="1176543210",
             tipo_piel="Tipo II (piel clara, pelo rubio)", alergias="Ninguna conocida",
             medicaciones_actuales="Ninguna",
             antecedentes="Sin antecedentes de relevancia."),
        dict(nombre="Miguel Ángel Herrera", dni="25789012", fecha_nacimiento=date(1972, 6, 3),
             sexo="Masculino", ocupacion="Médico cirujano", telefono="1165432109",
             tipo_piel="Tipo III", alergias="Sulfamidas",
             medicaciones_actuales="Atorvastatina 20mg",
             antecedentes="Nevus displásico extirpado en 2018 (benigno). Control anual."),
    ]

    CONSULTAS = [
        # Ana García — acné + seguimiento
        dict(paciente_idx=0, fecha=hoy - timedelta(days=3), proximo_control=hoy + timedelta(days=45),
             motivo="Acné inflamatorio en cara y espalda",
             duracion="2 años de evolución, empeoró en los últimos 3 meses",
             sintomas="Pápulas y pústulas dolorosas en mejillas, frente y zona superior de la espalda. Sin comedones cerrados importantes.",
             factores_desencadenantes="Estrés laboral, ciclo menstrual",
             zona_afectada="Cara (mejillas, frente, mentón), espalda superior",
             tipo_lesion="Pápulas", lesion_secundaria="Pústulas",
             severidad="Moderada", evolucion="Progresiva",
             diagnostico="Acné vulgar inflamatorio moderado",
             tratamiento="Adapaleno 0.1% gel + Clindamicina 1% gel (noche). Protector solar FPS50 diario.",
             recomendaciones="Evitar manipulación de lesiones. No usar productos oclusivos. Hidratante no comedogénico.",
             notas="Paciente muy motivada. Reevaluar en 6 semanas."),
        dict(paciente_idx=0, fecha=hoy - timedelta(days=1), proximo_control=hoy + timedelta(days=50),
             motivo="Control acné — respuesta a tratamiento",
             duracion="Seguimiento",
             sintomas="Reducción del 60% de lesiones inflamatorias. Leve descamación por adapaleno.",
             factores_desencadenantes="Buen cumplimiento del tratamiento",
             zona_afectada="Cara y espalda", tipo_lesion="Pápulas residuales",
             severidad="Leve", evolucion="Mejorando",
             diagnostico="Acné vulgar — buena respuesta terapéutica",
             tratamiento="Continuar esquema. Agregar hidratante reparador para la descamación.",
             recomendaciones="Mantener protector solar. Paciencia con el proceso.",
             notas="Excelente adherencia. Muy satisfecha con la evolución."),

        # Carlos Méndez — psoriasis
        dict(paciente_idx=1, fecha=hoy - timedelta(days=30), proximo_control=hoy + timedelta(days=60),
             motivo="Control de psoriasis en placas",
             duracion="5 años de diagnóstico. Brote actual desde hace 6 semanas.",
             sintomas="Placas eritematosas con escamas plateadas en codos, rodillas y cuero cabelludo. Prurito intenso nocturno.",
             factores_desencadenantes="Estrés laboral aumentado. Abandono de tratamiento tópico.",
             zona_afectada="Codos, rodillas, cuero cabelludo", tipo_lesion="Placas",
             severidad="Moderada-severa", evolucion="Brote activo",
             diagnostico="Psoriasis en placas, brote moderado-severo",
             diagnostico_diferencial="Dermatitis seborreica (cuero cabelludo)",
             estudios_solicitados="Laboratorio: hemograma, hepatograma, perfil lipídico (para evaluar inicio de metotrexato)",
             tratamiento="Corticoide tópico potente (clobetasol propionato 0.05%) en placas x 2 semanas. Champú de ketoconazol 2% en cuero cabelludo.",
             recomendaciones="Evitar traumatismos (fenómeno de Koebner). Emoliente abundante. Reducir estrés.",
             notas="Evaluar metotrexato si no mejora en 8 semanas."),

        # Laura Fernández — dermatitis atópica
        dict(paciente_idx=2, fecha=hoy - timedelta(days=60), proximo_control=hoy - timedelta(days=5),
             motivo="Dermatitis atópica — brote agudo",
             duracion="Brote desde hace 3 semanas. Atópica desde la infancia.",
             sintomas="Eccema agudo en pliegues antecubitales y poplíteos. Xerosis generalizada. Prurito intenso que interrumpe el sueño.",
             factores_desencadenantes="Cambio de jabón. Estrés. Invierno.",
             zona_afectada="Pliegues antecubitales, poplíteos, cuello",
             tipo_lesion="Placas eccematosas", lesion_secundaria="Excoriaciones por rascado",
             severidad="Moderada", evolucion="Brote activo",
             diagnostico="Dermatitis atópica, brote moderado",
             tratamiento="Metilprednisolona aceponato 0.1% crema x 10 días. Emoliente intensivo c/8hs. Antihistamínico nocturno.",
             recomendaciones="Baños cortos con agua tibia. Jabón syndet. Ropa de algodón.",
             notas="Control vencido — LLAMAR PARA REPROGRAMAR."),

        # Roberto Sosa — keratosis actínica
        dict(paciente_idx=3, fecha=hoy - timedelta(days=2), proximo_control=hoy + timedelta(days=160),
             motivo="Control anual. Revisión de queratosis actínicas.",
             duracion="Diagnóstico previo de QA hace 2 años.",
             sintomas="3 lesiones nuevas en zona calva (vértex). Ásperas al tacto, eritematosas.",
             factores_desencadenantes="Exposición solar crónica. Sin protector solar sistemático.",
             zona_afectada="Cuero cabelludo (vértex), dorso de manos",
             tipo_lesion="Máculas eritematosas con hiperqueratosis",
             severidad="Leve", evolucion="Estable con lesiones nuevas",
             diagnostico="Queratosis actínica múltiple",
             diagnostico_diferencial="Carcinoma espinocelular in situ (descartar en lesión mayor de mano derecha)",
             estudios_solicitados="Dermatoscopía de lesión en mano derecha. Eventual biopsia.",
             procedimientos="Crioterapia con nitrógeno líquido en 4 lesiones de cuero cabelludo.",
             tratamiento="Imiquimod 5% crema en campo de cancerización (mano derecha) x 4 semanas. Protector solar FPS100 diario.",
             recomendaciones="USO OBLIGATORIO de sombrero y protector solar. Controles semestrales.",
             notas="Paciente comprometido con el tratamiento luego de explicar riesgo de progresión."),

        # Valentina Torres — nevus
        dict(paciente_idx=4, fecha=hoy - timedelta(days=0), proximo_control=hoy + timedelta(days=355),
             motivo="Primera consulta. Revisión de manchas en espalda.",
             duracion="Lunares presentes desde la adolescencia. Sin cambios referidos.",
             sintomas="Múltiples nevus melanocíticos en tronco. Refiere uno en espalda alta que 'cambió de color'.",
             factores_desencadenantes="Exposición solar frecuente (verano en playa).",
             zona_afectada="Tronco, espalda, extremidades",
             tipo_lesion="Nevus melanocíticos", severidad="Sin signos de alarma",
             evolucion="Estable (por referencia)",
             observaciones_clinicas="Mapeado completo. Lesión referida: nevus compuesto, bordes regulares, color uniforme marrón claro. Dermatoscopía: red pigmentada regular.",
             diagnostico="Nevus melanocítico compuesto, sin signos de atipia. Fototipo II.",
             tratamiento="Sin tratamiento. Control clínico y fotográfico anual.",
             recomendaciones="Protector solar FPS50+ diario todo el año. Evitar exposición entre 10-16hs. Consultar ante cualquier cambio (ABCDE).",
             notas="Se realizó fotografía de referencia. Paciente educada sobre signos de alarma."),

        # Miguel Ángel — control oncológico
        dict(paciente_idx=5, fecha=hoy - timedelta(days=90), proximo_control=hoy + timedelta(days=275),
             motivo="Control anual. Antecedente de nevus displásico extirpado.",
             duracion="Seguimiento anual post-exéresis 2018.",
             sintomas="Sin lesiones nuevas de alarma. Sin síntomas.",
             factores_desencadenantes="Fotoexposición laboral moderada.",
             zona_afectada="Tronco, cara, extremidades (revisión completa)",
             tipo_lesion="Nevus melanocíticos múltiples",
             severidad="Sin signos de alarma", evolucion="Estable",
             observaciones_clinicas="Revisión completa de 47 lesiones pigmentadas. Sin signos ABCDE de atipia. Cicatriz de exéresis anterior: sin recidiva.",
             diagnostico="Nevus melanocíticos benignos múltiples. Antecedente de nevus displásico leve (extirpado 2018).",
             tratamiento="Sin tratamiento activo. Control anual obligatorio.",
             recomendaciones="Fotoprotección estricta. Autoexamen mensual. Consulta inmediata ante cambios.",
             notas="Médico muy informado. Excelente adherencia a controles."),
    ]

    pacientes_creados = []
    for p in PACIENTES:
        existente = db.query(models.Paciente).filter(models.Paciente.dni == p["dni"]).first()
        if not existente:
            nuevo = models.Paciente(**p)
            db.add(nuevo)
            db.flush()
            pacientes_creados.append(nuevo)
        else:
            pacientes_creados.append(existente)

    db.flush()

    for c in CONSULTAS:
        paciente = pacientes_creados[c.pop("paciente_idx")]
        consulta = models.Consulta(paciente_id=paciente.id, medico_id=medico_id, **c)
        db.add(consulta)

    db.commit()

    response = RedirectResponse(url="/pacientes", status_code=303)
    set_flash_message(response, f"✓ {len(PACIENTES)} pacientes demo cargados correctamente.")
    return response
