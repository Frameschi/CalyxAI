@echo off
REM Script para sincronizar la versión en todos los archivos
REM Uso: update_version.bat

cd /d "%~dp0"

REM Leer versión desde VERSION.txt
set /p VERSION=<VERSION.txt

echo Actualizando versión a: %VERSION%

REM Actualizar package.json
powershell -Command "(Get-Content frontend/package.json) -replace '\"version\": \"[^\"]*\"', '\"version\": \"%VERSION%\"' | Set-Content frontend/package.json"

REM Actualizar README.md
powershell -Command "(Get-Content README.md) -replace 'Versión [0-9]+\.[0-9]+\.[0-9]+', 'Versión %VERSION%' | Set-Content README.md"

echo Versión actualizada en todos los archivos!
echo.
echo Para actualizar la versión:
echo 1. Edita VERSION.txt con la nueva versión
echo 2. Ejecuta: update_version.bat
echo.
echo Archivos actualizados:
echo - VERSION.txt (manual)
echo - frontend/package.json (automático)
echo - README.md (automático)
echo - frontend/src/pages/Settings.tsx (dinámico desde backend)