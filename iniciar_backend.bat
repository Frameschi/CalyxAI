@echo off
cd /d "%~dp0calyx-ai\backend"
uvicorn main:app --reload
pause
