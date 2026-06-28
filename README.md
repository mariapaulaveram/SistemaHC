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
historias-clinicas/
├── app/
│   ├── main.py          # FastAPI app
│   ├── models.py        # Paciente, Consulta (SQLAlchemy)
│   ├── database.py      # conexión a Postgres
│   ├── routers/
│   │   ├── pacientes.py
│   │   └── consultas.py
│   └── templates/       # HTML con Jinja2
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## 6. Roadmap por etapas (cada etapa funciona antes de pasar a la siguiente)

### Etapa 0 — Setup base
- [ ] Dockerfile + docker-compose.yml (app + Postgres)
- [ ] Conexión de FastAPI a Postgres funcionando (`docker compose up`)
- [ ] Página de health-check (`/health`) para confirmar que todo levanta

### Etapa 1 — Pacientes
- [ ] Modelo de datos: Paciente (nombre, DNI, fecha de nacimiento, contacto,
  antecedentes)
- [ ] Alta de paciente (formulario)
- [ ] Listado y búsqueda de pacientes
- [ ] Ficha de paciente (vista de detalle)
- [ ] Edición de datos del paciente

### Etapa 2 — Consultas (el historial clínico en sí)
- [ ] Modelo de datos: Consulta (fecha, motivo, diagnóstico, tratamiento,
  notas, vinculada a un paciente)
- [ ] Agregar consulta desde la ficha del paciente
- [ ] Ver historial completo de consultas de un paciente, ordenado por fecha
- [ ] Editar/corregir una consulta ya cargada

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

## 7. Cómo se habla de esto en el CV / entrevista

- "Diseñé y desarrollé un sistema de historias clínicas electrónicas con
  FastAPI, PostgreSQL y Docker, en uso real por una médica."
- Permite hablar de: modelado de datos, autenticación, decisiones de
  arquitectura (por qué Jinja2+HTMX en vez de SPA), manejo de datos
  sensibles, deploy con contenedores.
- A diferencia de instalar un sistema ya hecho, todo el código y las
  decisiones son propias y se pueden explicar en detalle.

## 8. Próximo paso inmediato

Armar la Etapa 0: Dockerfile, docker-compose.yml, y la conexión inicial de
FastAPI con Postgres, para tener algo corriendo localmente antes de escribir
cualquier modelo de datos.