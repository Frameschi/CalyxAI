@echo off
cd /d "%~dp0\..\frontend"
start "Vite" cmd /c "npm run dev"
REM Esperar a que Vite esté listo y sirva HTML válido
:waitvite
powershell -Command "try { $r = Invoke-WebRequest -Uri http://localhost:5173 -UseBasicParsing } catch { $r = $null }; if ($r -eq $null -or $r.Content -notmatch '<title>') { Start-Sleep -Seconds 2; exit 1 }"
if errorlevel 1 goto waitvite
REM Cuando Vite esté listo, lanzar Electron
start "Electron" cmd /c "npm run start"
