@echo off
title Calyx AI Backend - DEBUG MODE
color 0A

echo.
echo ========================================
echo         CALYX AI BACKEND - DEBUG
echo ========================================
echo.

echo [DEBUG] Directorio actual: %~dp0
echo [DEBUG] Verificando si puerto 8000 esta ocupado...

netstat -ano | findstr :8000
if %errorlevel% equ 0 (
    echo [DEBUG] Puerto 8000 YA ESTA OCUPADO - Backend posiblemente ejecutandose
    echo [DEBUG] Cerrando en 5 segundos...
    timeout /t 5
    exit /b 0
) else (
    echo [DEBUG] Puerto 8000 LIBRE - Continuando...
)

echo.
echo [DEBUG] Buscando Python...

REM Probar Python commands comunes
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    echo [DEBUG] Python encontrado: python
    goto :found_python
)

python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python3
    echo [DEBUG] Python encontrado: python3
    goto :found_python
)

py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
    echo [DEBUG] Python encontrado: py
    goto :found_python
)

echo [ERROR] Python NO ENCONTRADO en el sistema
echo [ERROR] Por favor instala Python desde python.org
echo.
pause
exit /b 1

:found_python
echo [DEBUG] Usando comando Python: %PYTHON_CMD%
echo.

echo [DEBUG] Verificando directorio backend...
if not exist "%~dp0backend" (
    echo [ERROR] Directorio backend NO EXISTE: %~dp0backend
    echo [ERROR] Estructura del directorio:
    dir "%~dp0"
    pause
    exit /b 1
)

echo [DEBUG] Directorio backend OK: %~dp0backend
echo.

echo [DEBUG] Verificando archivo main.py...
if not exist "%~dp0backend\main.py" (
    echo [ERROR] Archivo main.py NO EXISTE: %~dp0backend\main.py
    echo [ERROR] Contenido del directorio backend:
    dir "%~dp0backend"
    pause
    exit /b 1
)

echo [DEBUG] Archivo main.py OK
echo.

echo [DEBUG] Instalando dependencias criticas...
echo [INFO] Ejecutando: %PYTHON_CMD% -m pip install fastapi uvicorn
%PYTHON_CMD% -m pip install --quiet fastapi uvicorn
if %errorlevel% neq 0 (
    echo [WARNING] Error al instalar dependencias basicas
    echo [INFO] Continuando de todas formas...
)

echo.
echo [DEBUG] Cambiando al directorio backend...
cd /d "%~dp0backend"
echo [DEBUG] Directorio actual: %CD%

echo.
echo [DEBUG] Iniciando servidor backend...
echo [INFO] Comando: %PYTHON_CMD% -m uvicorn main:app --host 0.0.0.0 --port 8000
echo [INFO] El servidor se iniciara ahora. Manten esta ventana abierta.
echo [INFO] Presiona Ctrl+C para detener el servidor.
echo.

%PYTHON_CMD% -m uvicorn main:app --host 0.0.0.0 --port 8000

echo.
echo [INFO] El servidor se detuvo.
pause
