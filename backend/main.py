from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sqlite3
from threading import Lock
from ai_engine import IAEngine
# Importar módulos de utilidades y cálculos
from utils.validators import validate_food_input
from calculos.nutricion import calcular_info_nutricional_basica, calcular_info_nutricional_completa

app = FastAPI()

# Habilitar CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instancia global del motor de IA - INICIALIZACIÓN DIFERIDA
ia_engine = None
ia_engine_lock = Lock()  # 🔒 Lock para sincronización de inicialización

def get_ia_engine():
    """Obtiene la instancia global de IAEngine con inicialización sincronizada"""
    global ia_engine
    with ia_engine_lock:  # 🔒 Sincronización para evitar inicializaciones múltiples
        if ia_engine is None:
            print("[DEBUG] Motor IA no inicializado, cargando ahora...")
            try:
                ia_engine = IAEngine()
                print("[DEBUG] Motor IA cargado exitosamente")
            except Exception as e:
                print(f"[ERROR] Error al cargar motor IA: {e}")
                ia_engine = None
    return ia_engine

def get_fallback_message():
    """Obtiene mensaje de fallback según el modelo activo"""
    try:
        ia_engine = get_ia_engine()
        if hasattr(ia_engine, 'current_model_key') and ia_engine.current_model_key == 'deepseek-r1':
            return "🧬 DeepSeek Nutrición Avanzada activado. Capacidad de análisis profundo y razonamiento nutricional disponible. ¿Qué consulta nutricional puedo analizar para ti?"
        else:
            return "¡Hola! Soy CalyxAI, tu asistente nutricional. ¿En qué puedo ayudarte hoy?"
    except:
        return "¡Hola! Soy CalyxAI, tu asistente nutricional. ¿En qué puedo ayudarte hoy?"

def parse_deepseek_response(response):
    """
    Parsea respuesta de DeepSeek-R1 para separar thinking del mensaje final.
    DeepSeek-R1 responde con: <think>razonamiento</think> mensaje final
    """
    import re
    
    # Buscar patrón <think> ... </think>
    think_pattern = r'<think>(.*?)</think>'
    match = re.search(think_pattern, response, re.DOTALL)
    
    if match:
        thinking_content = match.group(1).strip()
        # Remover el bloque <think> del mensaje final
        final_message = re.sub(think_pattern, '', response, flags=re.DOTALL).strip()
        return thinking_content, final_message
    else:
        # No hay thinking, devolver respuesta completa como mensaje final
        return None, response

# Función para consultar alimentos en la base de datos
def get_alimentos_by_name(nombre_busqueda, limite=5):
    """Consulta alimentos por nombre con búsqueda aproximada"""
    try:
        # Conectar a la base de datos
        db_path = os.path.join(os.path.dirname(__file__), "datainfo.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Función para quitar acentos
        def quitar_acentos(texto):
            import unicodedata
            return ''.join(c for c in unicodedata.normalize('NFD', texto)
                          if unicodedata.category(c) != 'Mn')

        # Preparar búsqueda sin acentos
        nombre_sin_acentos = quitar_acentos(nombre_busqueda.lower())

        # Consulta con búsqueda aproximada
        query = """
        SELECT * FROM alimentos
        WHERE LOWER(alimento) LIKE ?
        ORDER BY LENGTH(alimento) ASC
        LIMIT ?
        """

        cursor.execute(query, (f"%{nombre_sin_acentos}%", limite))
        rows = cursor.fetchall()

        # Obtener nombres de columnas
        column_names = [description[0] for description in cursor.description]

        conn.close()
        return column_names, rows

    except Exception as e:
        print(f"[ERROR] Error consultando alimentos: {e}")
        return [], []

@app.get("/")
def root():
    return {"message": "Calyx AI Backend - API de nutrición y consultas médicas"}

@app.get("/health")
def health():
    print("[LOG] /health endpoint called")
    try:
        ia_engine = get_ia_engine()
        return ia_engine.get_status()
    except Exception as e:
        print(f"[ERROR] Error getting IA engine status: {e}")
        return {"status": "error", "message": str(e), "ready": False}

@app.get("/ping")
async def ping():
    """Endpoint simple para verificar que el servidor funciona sin cargar el modelo"""
    return {"status": "ok", "message": "Calyx AI Backend is running"}

@app.post("/chat")
async def chat(request: Request):
    try:
        print("="*50)
        print("[LOG] /chat endpoint called")
        data = await request.json()
        print(f"[LOG] /chat received data: {data}")
        prompt = data.get("prompt", "").strip()
        print(f"[LOG] Prompt extraído: '{prompt}'")
        if not prompt:
            print("[LOG] /chat error: No prompt provided")
            return JSONResponse({"error": "No prompt provided"}, status_code=400)

        # --- SISTEMA DE TOOLS AUTOMÁTICO: El modelo decidirá cuándo consultar BD ---
        # El modelo DeepSeek-R1 tiene acceso a tools para consultar alimentos y fórmulas
        ia_engine = get_ia_engine()
        if ia_engine is None:
            return JSONResponse({"error": "AI engine not available"}, status_code=503)

        # Usar el sistema de tools para respuesta inteligente
        response = ia_engine.generate_with_tools(prompt, max_new_tokens=150, temperature=0.3)
        
        # Parsear respuesta de DeepSeek-R1 para separar thinking del mensaje final
        thinking_content, final_message = parse_deepseek_response(response)
        
        return {"message": final_message, "thinking": thinking_content, "console_block": None}

    except Exception as e:
        print(f"[LOG] /chat exception: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({"error": f"Error processing request: {str(e)}"}, status_code=500)

@app.get("/alimento")
def buscar_alimento(nombre: str = Query(..., description="Nombre del alimento a buscar")):
    print(f"[LOG] /alimento endpoint called with nombre={nombre}")

    if not nombre or len(nombre.strip()) < 2:
        return JSONResponse({"error": "Nombre de alimento requerido (mínimo 2 caracteres)"}, status_code=400)

    try:
        # Validar entrada
        validation = validate_food_input(nombre)
        if not validation["valid"]:
            return JSONResponse({"error": validation["message"]}, status_code=400)

        # Buscar en base de datos
        columns, rows = get_alimentos_by_name(nombre)

        if not columns or not rows:
            return JSONResponse({
                "error": f"No se encontraron alimentos que coincidan con '{nombre}'"
            }, status_code=404)

        # Procesar resultados
        filas = []
        variantes = []

        # Obtener el primer resultado (más relevante)
        alimento_dict = dict(zip(columns, rows[0]))

        # Determinar campos relevantes según el grupo de alimentos
        grupo = alimento_dict.get('grupo de alimentos', '').lower()

        campos_por_categoria = {
            "verduras": ["cantidad", "energia (kcal)", "fibra (g)"],
            "hortalizas": ["cantidad", "energia (kcal)", "fibra (g)"],
            "frutas": ["cantidad", "energia (kcal)", "fibra (g)", "vitamina c (mg)"],
            "cereales": ["cantidad", "energia (kcal)", "hidratos de carbono (g)", "fibra (g)"],
            "legumbres": ["cantidad", "energia (kcal)", "proteina (g)", "hidratos de carbono (g)"],
            "frutos secos": ["cantidad", "energia (kcal)", "lipidos (g)", "proteina (g)"],
            "carnes": ["cantidad", "energia (kcal)", "proteina (g)", "lipidos (g)"],
            "pescados": ["cantidad", "energia (kcal)", "proteina (g)", "lipidos (g)"],
            "lacteos": ["cantidad", "energia (kcal)", "proteina (g)", "calcio (mg)"],
            "huevos": ["cantidad", "energia (kcal)", "proteina (g)", "lipidos (g)"],
            "aceites": ["cantidad", "energia (kcal)", "lipidos (g)"],
            "bebidas": ["cantidad", "energia (kcal)", "hidratos de carbono (g)"],
            "azucares": ["cantidad", "energia (kcal)", "hidratos de carbono (g)"],
            "miscelaneos": ["cantidad", "energia (kcal)", "proteina (g)", "hidratos de carbono (g)", "lipidos (g)"]
        }

        # Campos por defecto si no se reconoce el grupo
        campos_default = ["cantidad", "energia (kcal)", "proteina (g)", "hidratos de carbono (g)", "lipidos (g)", "fibra (g)"]

        campos_relevantes = campos_por_categoria.get(grupo, campos_default)

        # Crear filas con campos relevantes
        info_basica = {
            "Alimento": alimento_dict.get('alimento', 'N/A'),
            "Grupo": alimento_dict.get('grupo de alimentos', 'N/A')
        }

        # Agregar campos relevantes
        for campo in campos_relevantes:
            if campo in alimento_dict:
                valor = alimento_dict[campo]
                # Formatear valores numéricos
                try:
                    if isinstance(valor, (int, float)) and valor != 0:
                        if campo == "cantidad":
                            info_basica[f"Porción base"] = f"{valor} {alimento_dict.get('unidad', 'g')}"
                        else:
                            info_basica[campo.title()] = f"{valor} {campo.split('(')[-1].rstrip(')') if '(' in campo else ''}"
                    else:
                        info_basica[campo.title()] = str(valor) if valor else "0"
                except:
                    info_basica[campo.title()] = str(valor) if valor else "N/A"

        filas = calcular_info_nutricional_basica(alimento_dict, info_basica)

        # Buscar variantes si hay más resultados
        if len(rows) > 1:
            for row in rows[1:3]:  # Máximo 2 variantes
                alt_dict = dict(zip(columns, row))
                variantes.append({
                    "alimento": alt_dict.get('alimento', ''),
                    "cantidad": f"{alt_dict.get('cantidad', 0)} {alt_dict.get('unidad', 'g')}",
                    "energia": f"{alt_dict.get('energia (kcal)', 0)} kcal"
                })

        mensaje = (
            f"Se encontró una coincidencia exacta para '{nombre}'."
            if not variantes else
            f"No se encontró una coincidencia exacta para '{nombre}'. Mostrando la opción más similar y algunas variantes."
        )

        return {
            "filas": filas,
            "mensaje": mensaje,
            "sugerencias": variantes
        }

    except Exception as e:
        print(f"[LOG] /alimento exception: {e}")
        return JSONResponse({"error": f"Error interno del servidor: {str(e)}"}, status_code=500)

# Variables globales para el progreso de inicio del backend
backend_startup_status = {
    "status": "ready",  # ready, loading, error
    "progress_percentage": 100,
    "current_step": "Backend listo y funcionando",
    "total_steps": 4,
    "current_step_number": 4,
    "error_message": ""
}

@app.get("/backend/startup/progress")
async def get_backend_startup_progress():
    """Endpoint para obtener el progreso de inicio del backend"""
    global backend_startup_status
    return backend_startup_status

@app.get("/model/current")
def get_current_model():
    """Obtener información del modelo actual"""
    try:
        ia_engine = get_ia_engine()
        return ia_engine.get_current_model()
    except Exception as e:
        return {"error": f"Error al obtener información del modelo: {str(e)}"}

@app.get("/model/status")
def get_model_status():
    """Endpoint para verificar el estado del modelo"""
    try:
        ia_engine = get_ia_engine()
        status = ia_engine.get_status()
        return {
            "model_name": status.get("model_name", "Unknown"),
            "device": status.get("device", "Unknown"),
            "is_downloaded": status.get("is_downloaded", False),
            "cache_size_mb": status.get("cache_size_mb", 0),
            "cache_path": status.get("cache_path", ""),
            "status": status.get("status", "Unknown"),
            "message": status.get("message", ""),
            "ready": status.get("ready", False)
        }
    except Exception as e:
        return {
            "error": f"Error al verificar el estado del modelo: {str(e)}",
            "model_name": "Unknown",
            "device": "Unknown",
            "is_downloaded": False,
            "cache_size_mb": 0,
            "cache_path": "",
            "status": "error",
            "message": str(e),
            "ready": False
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)