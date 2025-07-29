@echo off
setlocal

REM === Rutas ===
set PROJECT_DIR=C:\WorkSpace\sistema_tareas
set BACKUP_DIR=%PROJECT_DIR%\backups

REM === Fecha y hora ===
for /f "tokens=1-4 delims=/ " %%a in ("%date%") do (
    set day=%%a
    set month=%%b
    set year=%%c
)
for /f "tokens=1-2 delims=: " %%a in ("%time%") do (
    set hour=%%a
    set min=%%b
)

REM === Reemplazar : por - para el nombre del archivo ===
set FILE_NAME=db_backup_%year%-%month%-%day%_%hour%-%min%.sqlite3

REM === Crear carpeta si no existe ===
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

REM === Copiar base de datos ===
copy "%PROJECT_DIR%\db.sqlite3" "%BACKUP_DIR%\%FILE_NAME%"

echo Backup creado: %FILE_NAME%
