# ============================================================
# HC-System — Restaurar backup
# Uso: .\restore.ps1 -Archivo "hc_backup_2026-07-03_08-00.sql"
# ============================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$Archivo
)

$GOOGLE_DRIVE = "$env:USERPROFILE\Google Drive\Mi unidad\HC-System-Backups"
$PROYECTO     = "C:\Users\trezz\Desktop\proyectosDeDesarrolloWeb\SistemaHC"
$DB_USER      = "user"
$DB_NAME      = "historias_db"

$ruta = Join-Path $GOOGLE_DRIVE $Archivo
if (-not (Test-Path $ruta)) {
    Write-Error "Archivo no encontrado: $ruta"
    exit 1
}

Write-Host "ATENCIÓN: Esto va a reemplazar TODOS los datos actuales con el backup."
Write-Host "Archivo: $Archivo"
$confirmacion = Read-Host "Escribí 'SI' para confirmar"
if ($confirmacion -ne "SI") {
    Write-Host "Restauración cancelada."
    exit 0
}

Write-Host "Restaurando backup..."

# Leer el SQL y pasarlo al contenedor
Get-Content $ruta -Raw | & docker compose --project-directory $PROYECTO exec -T db `
    psql -U $DB_USER -d $DB_NAME

if ($LASTEXITCODE -ne 0) {
    Write-Error "ERROR al restaurar. Revisá los mensajes de arriba."
    exit 1
}

Write-Host "Restauración completada exitosamente."
