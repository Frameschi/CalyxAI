@echo off
echo 🚀 Iniciando Calyx AI Backend con DeepSeek-R1...
echo.

cd /d "%~dp0"

echo 📦 Verificando dependencias de Python...
python -c "import ollama, fastapi, torch; print('✅ Dependencias OK')" 2>nul
if errorlevel 1 (
    echo ❌ Faltan dependencias. Ejecuta: pip install -r requirements.txt
    pause
    exit /b 1
)

echo 🔧 Verificando Ollama service...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo ❌ Ollama no está ejecutándose. Inicia Ollama primero.
    echo 💡 Ejecuta: ollama serve
    pause
    exit /b 1
)

echo ✅ Ollama service activo

echo 🤖 Verificando modelo DeepSeek-R1...
python -c "import ollama; client=ollama.Client(); models=client.list(); model_names=[m.model for m in models.models]; print('Modelos:', model_names); assert 'hf.co/unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF:Q4_K_M' in model_names" 2>nul
if errorlevel 1 (
    echo ❌ Modelo DeepSeek-R1 no encontrado. Descargando...
    ollama pull hf.co/unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF:Q4_K_M
    if errorlevel 1 (
        echo ❌ Error al descargar modelo
        pause
        exit /b 1
    )
)

echo ✅ Modelo DeepSeek-R1 listo

echo 🚀 Iniciando servidor FastAPI...
python main.py