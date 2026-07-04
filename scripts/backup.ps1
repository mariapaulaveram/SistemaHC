# ============================================================
# HC-System — Backup automático de base de datos
# Guarda un .sql en tu carpeta de Google Drive
# ============================================================

# ── CONFIGURACIÓN ────────────────────────────────────────────
# Cambiá esta ruta a tu carpeta de Google Drive
$GOOGLE_DRIVE = "$env:USERPROFILE\Google Drive\Mi unidad\HC-System-Backups"

# Cuántos backups mantener (borra los más viejos)
$BACKUPS_A_MANTENER = 30

# Directorio donde está el docker-compose.yml
$PROYECTO = "C:\Users\trezz\Desktop\proyectosDeDesarrolloWeb\SistemaHC"

# Credenciales de la DB (deben coincidir con tu docker-compose.yml)
$DB_USER = "user"
$DB_NAME = "historias_db"
# ─────────────────────────────────────────────────────────────

$fecha    = Get-Date -Format "yyyy-MM-dd_HH-mm"
$archivo  = "hc_backup_$fecha.sql"
$destino  = Join-Path $GOOGLE_DRIVE $archivo

# Crear carpeta de destino si no existe
if (-not (Test-Path $GOOGLE_DRIVE)) {
    New-Item -ItemType Directory -Path $GOOGLE_DRIVE -Force | Out-Null
    Write-Host "Carpeta creada: $GOOGLE_DRIVE"
}

Write-Host "[$fecha] Iniciando backup de HC-System..."

# Correr pg_dump dentro del contenedor de Docker
$resultado = & docker compose --project-directory $PROYECTO exec -T db `
    pg_dump -U $DB_USER $DB_NAME 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Error "ERROR: pg_dump falló. ¿Está corriendo el contenedor?"
    Write-Error $resultado
    exit 1
}

# Guardar el archivo SQL
$resultado | Out-File -FilePath $destino -Encoding UTF8

$tamano = [math]::Round((Get-Item $destino).Length / 1KB, 1)
Write-Host "Backup guardado: $archivo ($tamano KB)"

# ── Limpiar backups viejos ────────────────────────────────────
$backups = Get-ChildItem -Path $GOOGLE_DRIVE -Filter "hc_backup_*.sql" |
           Sort-Object CreationTime -Descending

if ($backups.Count -gt $BACKUPS_A_MANTENER) {
    $aEliminar = $backups | Select-Object -Skip $BACKUPS_A_MANTENER
    foreach ($archivo in $aEliminar) {
        Remove-Item $archivo.FullName -Force
        Write-Host "Eliminado backup viejo: $($archivo.Name)"
    }
}

Write-Host "Backup completado exitosamente."
