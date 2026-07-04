# HC-System — Sistema de Historias Clínicas

Sistema web de historias clínicas electrónicas para uso real en consultorio de dermatología. Desarrollado de punta a punta con FastAPI, PostgreSQL y Docker.

## ¿Qué hace?

- Alta, búsqueda y gestión de pacientes con datos clínicos dermatológicos
- Historia clínica completa por paciente: anamnesis, examen dermatológico, diagnóstico y plan terapéutico
- Registro fotográfico de lesiones por consulta
- Calendario de próximos controles
- Exportación a Excel y CSV
- Impresión de ficha clínica
- Múltiples usuarios con roles (admin / médico)
- Dashboard clínico con alertas de controles vencidos y próximos
- Backups automáticos de la base de datos

## Stack

| Capa | Tecnología | Motivo |
|---|---|---|
| Backend | FastAPI (Python) | Moderno, tipado, rápido de desarrollar |
| Base de datos | PostgreSQL | Estándar de producción |
| ORM | SQLAlchemy | Modelo de datos en Python, sin SQL a mano |
| Frontend | Jinja2 + HTMX | Un solo proyecto, sin build step, sin CORS |
| Auth | Sesiones firmadas + bcrypt + CSRF | Seguridad real sin JWT overhead |
| Infraestructura | Docker + docker-compose | Portable, reproducible, deployable |

## Estructura del proyecto

```
SistemaHC/
├── app/
│   ├── main.py              # FastAPI app, dashboard, calendario
│   ├── models.py            # Paciente, Consulta, Usuario, ImagenConsulta
│   ├── schemas.py           # Esquemas Pydantic
│   ├── database.py          # Conexión a PostgreSQL
│   ├── auth.py              # Sesiones, bcrypt, CSRF, roles
│   ├── utils.py             # Flash messages, render helper, filtros Jinja2
│   ├── routers/
│   │   ├── auth.py          # Login / logout
│   │   ├── pacientes.py     # CRUD pacientes + exportar Excel/CSV
│   │   ├── consultas.py     # CRUD consultas + fotos
│   │   ├── imagenes.py      # Subida y eliminación de fotos
│   │   ├── admin.py         # Panel de administración de usuarios
│   │   └── perfil.py        # Cambio de nombre y contraseña
│   ├── static/css/          # Estilos (responsive, diseño profesional)
│   └── templates/           # HTML con Jinja2
│       ├── base.html
│       ├── index.html           # Dashboard
│       ├── login.html
│       ├── lista_pacientes.html
│       ├── paciente_detalle.html
│       ├── paciente_editar.html
│       ├── paciente_imprimir.html
│       ├── consulta_detalle.html
│       ├── consulta_editar.html
│       ├── calendario.html
│       ├── admin_usuarios.html
│       └── perfil.html
├── scripts/
│   ├── crear_usuario.py     # Crear usuario admin desde CLI
│   ├── backup.ps1           # Backup automático a Google Drive (Windows)
│   └── restore.ps1          # Restaurar backup
├── nginx/
│   └── nginx.conf           # Reverse proxy + HTTPS para producción
├── docker-compose.yml       # Desarrollo local
├── docker-compose.prod.yml  # Producción (incluye Nginx + Certbot)
├── .env.prod.example        # Template de variables de entorno
├── DEPLOY.md                # Guía de deploy paso a paso
├── Dockerfile
└── requirements.txt
```

## Correr en local

```bash
git clone <repo> SistemaHC
cd SistemaHC
docker compose up -d
```

El sistema queda disponible en `http://localhost:8000`.

### Crear el primer usuario

```bash
docker compose exec web python scripts/crear_usuario.py
```

## Deploy en producción

Ver [DEPLOY.md](DEPLOY.md) para la guía completa con Nginx + HTTPS (Let's Encrypt).

## Seguridad implementada

- Contraseñas con bcrypt (nunca en texto plano)
- Sesiones firmadas con `itsdangerous` (HMAC)
- Protección CSRF en todos los formularios
- Uploads de imágenes servidos solo a usuarios autenticados
- Roles: admin puede gestionar usuarios, médico solo accede al sistema clínico
- Headers de seguridad en Nginx (HSTS, X-Frame-Options, X-Content-Type-Options)

## Backups

Script PowerShell (`scripts/backup.ps1`) que hace `pg_dump` del contenedor Docker y guarda el `.sql` en Google Drive. Programado en el Programador de Tareas de Windows para correr diariamente. Mantiene los últimos 30 días y borra los más viejos automáticamente.

## Estado del proyecto

- [x] Gestión completa de pacientes y consultas
- [x] Registro fotográfico de lesiones
- [x] Autenticación y seguridad
- [x] Múltiples usuarios con roles
- [x] Dashboard clínico con alertas
- [x] Calendario de controles
- [x] Exportación Excel / CSV
- [x] Impresión de ficha
- [x] Responsive para tablet
- [x] Backups automáticos
- [x] Configuración de producción lista (Nginx + Certbot)
- [ ] Deploy en VPS con HTTPS

## Autoría

Desarrollado por **Maria Paula Veram** con asistencia de [Claude](https://claude.ai) (Anthropic) para acelerar el desarrollo.

Las decisiones de arquitectura, el diseño del modelo de datos, los requisitos clínicos y la dirección del proyecto son propios. Claude funcionó como herramienta de desarrollo — equivalente a un pair programmer — generando y revisando código bajo criterio propio.

## Licencia

MIT — ver [LICENSE](LICENSE).
