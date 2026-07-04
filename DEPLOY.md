# Guía de deploy — HC-System

## Requisitos
- VPS Ubuntu 22/24 con Docker instalado
- Dominio apuntando a la IP del VPS
- Puerto 80 y 443 abiertos en el firewall

## Primera vez en servidor nuevo

### 1. Subir el código
```bash
git clone <repo> SistemaHC
cd SistemaHC
```

### 2. Crear variables de entorno
```bash
cp .env.prod.example .env.prod
nano .env.prod   # completar SECRET_KEY y DB_PASSWORD
```

Generá una SECRET_KEY segura con:
```bash
openssl rand -hex 32
```

### 3. Reemplazar el dominio en nginx
```bash
sed -i 's/TU_DOMINIO.com/tudominio.com/g' nginx/nginx.conf
```

### 4. Levantar el sistema
```bash
docker compose -f docker-compose.prod.yml up -d
```

SQLAlchemy crea todas las tablas automáticamente en el primer arranque.
**No necesitás correr migraciones en un servidor nuevo.**

### 5. Obtener certificado SSL (Let's Encrypt)
```bash
docker compose -f docker-compose.prod.yml run --rm certbot \
  certonly --webroot --webroot-path /var/www/certbot \
  -d tudominio.com -d www.tudominio.com \
  --email tu@email.com --agree-tos --no-eff-email
```

### 6. Reiniciar nginx para cargar el certificado
```bash
docker compose -f docker-compose.prod.yml restart nginx
```

### 7. Crear el primer usuario administrador
```bash
docker compose -f docker-compose.prod.yml exec web \
  python scripts/crear_usuario.py
```

---

## Migraciones (solo en DB existente con datos previos)

Necesitás correr migraciones solo si actualizás un servidor que ya tenía datos.

### v2 — Múltiples usuarios (roles + médico por consulta)
```bash
docker compose exec db psql -U user -d historias_db -c "
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS rol VARCHAR NOT NULL DEFAULT 'medico';
ALTER TABLE consultas ADD COLUMN IF NOT EXISTS medico_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL;
UPDATE usuarios SET rol = 'admin' WHERE id = 1;"
```

---

## Backups

El script `scripts/backup.ps1` corre en Windows y guarda en Google Drive.
En Linux/servidor:

```bash
docker compose exec db pg_dump -U user historias_db > backup_$(date +%Y%m%d).sql
```

Para restaurar:
```bash
cat backup.sql | docker compose exec -T db psql -U user -d historias_db
```

---

## Actualizar el sistema (nueva versión)

```bash
git pull
docker compose -f docker-compose.prod.yml build web
docker compose -f docker-compose.prod.yml up -d
# Si hay migraciones nuevas, correrlas acá
```
