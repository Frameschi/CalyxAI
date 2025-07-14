
from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import os
import sqlite3
from ai_engine import IAEngine



app = FastAPI()

# Habilitar CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)






# Instancia global del motor de IA
ia_engine = IAEngine()
@app.get("/health")
def health():
    print("[LOG] /health endpoint called")
    return ia_engine.get_status()

# Ruta de la base de datos de alimentos
DB_PATH = "datainfo.db"
def get_alimentos_by_name(nombre: str):
    import unicodedata
    def quitar_acentos(texto):
        return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    try:
        conn = sqlite3.connect(DB_PATH, timeout=3)
        conn.create_function("NOACCENTS", 1, quitar_acentos)
        cursor = conn.cursor()
        # Búsqueda flexible: sin acentos y sin distinción de mayúsculas/minúsculas
        cursor.execute("SELECT * FROM alimentos WHERE NOACCENTS(LOWER(alimento)) LIKE NOACCENTS(LOWER(?))", (f"%{nombre}%",))
        rows = cursor.fetchall()
        # Obtener columnas
        cursor.execute("PRAGMA table_info(alimentos);")
        columns = [col[1] for col in cursor.fetchall()]
        conn.close()
        return columns, rows
    except Exception as e:
        return None, None

def get_mas_comun(rows, nombre_busqueda=None):
    # Prioridad: si hay coincidencia exacta, devolver esa, si no, la primera
    if nombre_busqueda:
        for row in rows:
            if row[1].strip().lower() == nombre_busqueda.strip().lower():
                return row
    return rows[0] if rows else None

@app.get("/alimento")
def buscar_alimento(nombre: str = Query(..., description="Nombre del alimento a buscar")):
    print(f"[LOG] /alimento endpoint called with nombre={nombre}")
    # Detectar si es petición de información completa y extraer el nombre real
    import unicodedata
    def limpiar_nombre(texto):
        texto = texto.lower()
        texto = texto.replace("informacion completa de", "").replace("información completa de", "")
        texto = texto.replace("informacion de", "").replace("información de", "")
        texto = texto.replace("completa de", "")
        texto = texto.replace("completa", "")
        texto = texto.replace("de ", "") if texto.startswith("de ") else texto
        texto = texto.strip()
        texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
        return texto

    nombre_busqueda = limpiar_nombre(nombre)
    es_completa = "completa" in nombre.lower()

    columns, rows = get_alimentos_by_name(nombre_busqueda)
    if columns is None or rows is None:
        return {"error": "Error al consultar la base de datos de alimentos. Intenta de nuevo más tarde."}
    if not rows:
        return {"error": f"No se encontró información para '{nombre_busqueda}'"}

    # Coincidencia exacta ignorando acentos y mayúsculas
    def comparar_flexible(a, b):
        a = limpiar_nombre(a)
        b = limpiar_nombre(b)
        return a == b

    def get_mas_comun_flexible(rows, nombre_busqueda=None):
        if nombre_busqueda:
            for row in rows:
                if comparar_flexible(row[1], nombre_busqueda):
                    return row
        return rows[0] if rows else None

    mas_comun = get_mas_comun_flexible(rows, nombre_busqueda)
    variantes = [row[1] for row in rows if row != mas_comun]

    alimento_dict = dict(zip(columns, mas_comun))
    if es_completa:
        alimento_filtrado = {k.title(): v for k, v in alimento_dict.items() if k.lower() != "id"}
    else:
        campos_mostrar = {
            "cantidad": "Cantidad",
            "energia (kcal)": "Energía (kcal)",
            "fibra (g)": "Fibra (g)"
        }
        alimento_filtrado = {nuevo: alimento_dict[original] for original, nuevo in campos_mostrar.items() if original in alimento_dict}

    resultado = {
        "alimento_principal": alimento_filtrado,
        "sugerencias": variantes
    }
    return resultado


@app.post("/chat")
async def chat(request: Request):
    print("[LOG] /chat endpoint called")
    data = await request.json()
    print(f"[LOG] /chat received data: {data}")
    prompt = data.get("prompt", "").strip()
    if not prompt:
        print("[LOG] /chat error: No prompt provided")
        return JSONResponse({"error": "No prompt provided"}, status_code=400)

    # Detectar si el prompt menciona un alimento de la base
    # Usar la misma lógica de limpieza que en buscar_alimento
    import unicodedata
    def limpiar_nombre(texto):
        texto = texto.lower()
        texto = texto.replace("informacion completa de", "").replace("información completa de", "")
        texto = texto.replace("informacion de", "").replace("información de", "")
        texto = texto.replace("completa de", "")
        texto = texto.replace("completa", "")
        texto = texto.replace("de ", "") if texto.startswith("de ") else texto
        texto = texto.strip()
        texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
        return texto

    alimento_mencionado = limpiar_nombre(prompt)
    columns, rows = get_alimentos_by_name(alimento_mencionado)
    contexto_extra = ""
    # Detectar si el prompt trata sobre nutrición, alimentos o cálculos
    temas_nutricion = ["alimento", "caloría", "proteína", "fibra", "vitamina", "mineral", "nutrición", "formula", "cálculo", "energía", "macronutriente", "micronutriente"]
    es_nutricion = any(t in prompt.lower() for t in temas_nutricion)

    if rows and es_nutricion:
        # Si se encuentra el alimento y el tema es nutricional, preparar contexto nutricional
        mas_comun = rows[0]
        alimento_dict = dict(zip(columns, mas_comun))
        contexto_extra = f"\nDatos nutricionales de '{alimento_dict.get('alimento', alimento_mencionado)}':\n"
        for k, v in alimento_dict.items():
            if k.lower() != "id":
                contexto_extra += f"- {k.title()}: {v}\n"
        if "completa" in prompt.lower():
            contexto_extra += "\nPor favor, proporciona toda la información nutricional relevante.\n"
        else:
            contexto_extra += "\nPor favor, responde solo con los datos más relevantes para el usuario.\n"
    elif es_nutricion:
        # Si el tema es nutricional pero no hay alimento en la base, dar instrucción para usar solo datos confiables
        contexto_extra = "\nResponde solo con información nutricional basada en la base de datos proporcionada. Si no tienes datos, indica que no puedes responder con precisión.\n"
    # Si no es tema de nutrición, no agregar contexto extra: Phi-3 actúa como asistente general

    prompt_final = prompt + contexto_extra
    if not ia_engine.is_ready():
        status = ia_engine.get_status()
        print(f"[LOG] /chat error: IA engine not ready: {status['message']}")
        return JSONResponse({"error": status["message"]}, status_code=503 if status["status"]=="loading" else 500)
    try:
        response = ia_engine.generate(prompt_final)
        print(f"[LOG] /chat response: {response}")
        return {"response": response}
    except Exception as e:
        print(f"[LOG] /chat exception: {e}")
        return JSONResponse({"error": f"Ocurrió un error al generar la respuesta: {str(e)}"}, status_code=500)


@app.get("/")
def root():
    return {"message": "Calyx AI backend activo (Phi-3 Mini-4K-Instruct)"}
