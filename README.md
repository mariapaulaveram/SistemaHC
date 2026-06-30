# Sistema de Historias Clínicas — Plan de trabajo y ayuda memoria

## 1. Objetivo del proyecto

Construir un sistema simple de historias clínicas electrónicas para uso real de
mi hermana (médica), accesible desde internet sin importar en qué consultorio
o lugar esté atendiendo. Un solo sistema centralizado, no sincronización entre
sistemas distintos.

**Objetivos en paralelo:**
- Resolver un problema real: que mi hermana pueda cargar y consultar el
  historial de sus pacientes desde cualquier lugar.
- Tener un proyecto propio, real y usado, para mostrar en el CV como mejora /
  implementación hecha de punta a punta.

## 2. Decisiones de alcance (por qué este proyecto y no otro)

- **No se construye un LIMS de laboratorio** (se descartó Beak LIMS — el repo
  desapareció, riesgo típico de proyectos de un solo mantenedor).
- **No se usa un EHR/LIMS maduro ya armado** (Senaite, OpenEMR, GNU Health).
  Son sólidos para uso real en producción, pero:
  - Corren en stacks de nicho (Plone/Zope, Tryton, LAMP) alejados de lo que
    quiero aprender y mostrar (Python moderno).
  - Instalar uno tal cual no demuestra trabajo de desarrollo propio para CV.
  - Son mucho más grandes de lo que mi hermana necesita hoy.
- **Se construye un sistema propio, chico y a medida**, usando esos sistemas
  maduros solo como referencia de qué campos/flujos tiene una historia clínica
  real (para no improvisar la estructura de datos).

## 3. Stack elegido y por qué

| Capa | Tecnología | Motivo |
|---|---|---|
| Backend | FastAPI (Python) | Stack moderno, mismo lenguaje de punta a punta |
| Base de datos | PostgreSQL | Estándar real de producción, no un juguete tipo SQLite |
| ORM | SQLAlchemy | Modelo de datos en código Python, sin SQL a mano |
| Frontend | Jinja2 + HTMX | Sin proyecto separado, sin build step, sin CORS — mucho menos trabajoso que React + Node |
| Auth | Sesiones + bcrypt | Login simple, contraseña nunca en texto plano |
| Infraestructura | Docker + docker-compose | Portable, mostrable en CV, fácil de mover a un servidor real después |

**Por qué no React + Node de nuevo:** evita tener dos proyectos separados
hablándose entre sí (API + SPA), build steps, manejo de estado en cliente y
configuración de CORS. Con FastAPI + Jinja2 + HTMX es un solo proyecto: una
función en Python devuelve HTML, HTMX agrega interactividad sin escribir JS.

## 4. Cosas a tener en cuenta desde el día 1 (no como parche al final)

- Es información de salud de pacientes reales: contraseñas siempre hasheadas,
  nunca loguear datos de pacientes en texto plano, cuidado con mensajes de
  error que expongan datos.
- Pensar en HTTPS desde que se despliegue en un servidor real (no en local).
- Backups de la base de datos una vez que haya datos reales cargados.

## 5. Estructura del proyecto

```
SistemaHC/
├── app/
│   ├── main.py            # FastAPI app + dashboard
│   ├── models.py          # Paciente, Consulta (SQLAlchemy)
│   ├── schemas.py         # Esquemas Pydantic (para la API JSON)
│   ├── database.py        # conexión a Postgres
│   ├── utils.py           # flash messages, helper de render
│   ├── routers/
│   │   ├── pacientes.py
│   │   └── consultas.py
│   ├── static/css/        # estilos (paleta azul/blanco, sobria)
│   └── templates/         # HTML con Jinja2 + HTMX
├── scripts/                # scripts de prueba manual (no entran en la imagen Docker)
├── docker-compose.yml
├── Dockerfile
├── .gitignore
├── .dockerignore
└── requirements.txt
```

**Nota:** el modelo de `Paciente` se amplió respecto al plan original con campos
dermatológicos (tipo de piel, alergias, medicaciones actuales), y el de
`Consulta` con campos clínicos específicos de dermatología (zona afectada,
tipo de lesión, severidad, evolución). Surgió al construir, tiene sentido
para el caso de uso real de mi hermana (dermatóloga).

## 6. Roadmap por etapas (cada etapa funciona antes de pasar a la siguiente)

### Etapa 0 — Setup base ✅ Completa
- [x] Dockerfile + docker-compose.yml (app + Postgres)
- [x] Conexión de FastAPI a Postgres funcionando (`docker compose up`)
- [x] Volumen persistente de Postgres (los datos sobreviven a recrear contenedores)

### Etapa 1 — Pacientes ✅ Completa
- [x] Modelo de datos: Paciente (nombre, DNI, fecha de nacimiento, contacto,
  antecedentes + campos dermatológicos: tipo de piel, alergias, medicaciones)
- [x] Alta de paciente (formulario, página propia `/pacientes/nuevo`)
- [x] Listado y búsqueda de pacientes (por nombre o DNI exacto, con redirect
  directo a la ficha si el DNI matchea)
- [x] Filtros adicionales: por tipo de piel, por presencia de antecedentes
- [x] Ordenamiento (por nombre, DNI o fecha de nacimiento, asc/desc)
- [x] Ficha de paciente (vista de detalle)
- [x] Edición de datos del paciente

### Etapa 2 — Consultas (el historial clínico en sí) ✅ Completa
- [x] Modelo de datos: Consulta (fecha, motivo, diagnóstico, tratamiento,
  notas + campos dermatológicos: zona afectada, tipo de lesión, severidad,
  evolución, observaciones clínicas, recomendaciones)
- [x] Agregar consulta desde la ficha del paciente
- [x] Ver historial completo de consultas de un paciente, ordenado por fecha
- [x] Ver detalle de una consulta individual
- [x] Editar/corregir una consulta ya cargada

### Etapa 3 — Login y seguridad
- [ ] Modelo de Usuario (mi hermana, por ahora una sola cuenta)
- [ ] Login con sesión
- [ ] Proteger todas las rutas de pacientes/consultas detrás del login
- [ ] Logout

### Etapa 4 — Extra para portfolio (elegir una)
- [ ] Opción A: Exportar historial de un paciente a PDF
- [ ] Opción B: Dashboard simple (consultas por mes, diagnósticos más
  frecuentes) usando Pandas

### Etapa 5 — Deploy
- [ ] Subir el código a un repo de GitHub propio
- [ ] Deploy en un hosting (Railway, Render o un VPS chico)
- [ ] Probar que mi hermana pueda entrar desde su celular/notebook con
  internet, desde cualquier lugar
- [ ] README claro en el repo (qué es, stack, cómo correrlo) — esto también
  suma para CV

## 7. Auditoría de código (junio 2026)

Antes de avanzar a login y deploy, se hizo una revisión completa del código
existente — corriendo cada flujo de verdad (no solo leyendo), para encontrar
bugs reales antes de construir más funcionalidad encima.

**Bugs corregidos:**
- 🔴 **Crítico:** el `docker-compose.yml` no tenía volumen persistente para
  Postgres — cualquier recreación del contenedor borraba todos los datos.
  Se agregó un volumen nombrado (`db_data`).
- 🟠 Los campos vacíos de paciente/consulta se mostraban como el texto
  literal `"None"` en los formularios de edición (bug de Jinja2 al imprimir
  valores `None` sin manejar). Corregido en `paciente_editar.html` y
  `consulta_editar.html`.
- 🟡 Referencia a un archivo `forms.css` que no existía y nunca se cargaba
  (código muerto de una iteración anterior). Eliminada.

**Mejoras de infraestructura y mantenibilidad:**
- Se agregó `.gitignore` (faltaba) y se sacaron del repo 18 archivos
  `__pycache__` que se habían colado en commits anteriores.
- Se agregó `.dockerignore` para que la imagen de Docker no copie `.venv`,
  `.git` y archivos de prueba locales (eran ~45 MB de más en cada build).
- Se fijaron las versiones exactas en `requirements.txt` (antes sin pinear),
  probadas de punta a punta antes de fijarlas, para builds reproducibles.
- Se ordenaron los scripts de prueba manual en `scripts/`, separados del
  código de producción.

## 8. Cómo se habla de esto en el CV / entrevista

- "Diseñé y desarrollé un sistema de historias clínicas electrónicas con
  FastAPI, PostgreSQL y Docker, en uso real por una médica."
- Permite hablar de: modelado de datos, autenticación, decisiones de
  arquitectura (por qué Jinja2+HTMX en vez de SPA), manejo de datos
  sensibles, deploy con contenedores.
- A diferencia de instalar un sistema ya hecho, todo el código y las
  decisiones son propias y se pueden explicar en detalle.
- La auditoría de código (sección 7) también es material de entrevista: poder
  explicar cómo se encontró y corrigió un riesgo real de pérdida de datos
  (volumen de Docker faltante) antes de que pasara con datos de pacientes
  reales, demuestra criterio, no solo capacidad de escribir código nuevo.

## 9. Próximo paso inmediato

Etapas 0, 1 y 2 completas y auditadas. Lo que sigue:
- **Etapa 3** — Login y seguridad (todavía no empezada: el sistema hoy es
  accesible sin autenticación, válido para desarrollo local pero no para
  producción).
- **Etapa 4** — Elegir entre exportar a PDF o dashboard con Pandas.
- **Etapa 5** — Deploy a un hosting real con Postgres administrado (Railway,
  Render, Supabase o Neon), para que sea accesible desde cualquier lugar
  con internet, no solo en `localhost`.