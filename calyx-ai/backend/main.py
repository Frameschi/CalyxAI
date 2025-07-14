
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


    # Detectar cantidad y unidad en la consulta (ej: "180g de pollo cocido")
    import re
    cantidad_detectada = None
    unidad_detectada = None
    nombre_sin_cantidad = nombre
    match_cant = re.search(r"(\d+(?:[\.,]\d+)?)(\s*)(g|gramos|kg|kilos|ml|l|litros|mg)?\s+de\s+(.+)", nombre.lower())
    if match_cant:
        cantidad_detectada = float(match_cant.group(1).replace(",","."))
        unidad_detectada = match_cant.group(3) or "g"
        nombre_sin_cantidad = match_cant.group(4)
    else:
        # Buscar "de [alimento]" sin cantidad
        match_simple = re.search(r"de\s+(.+)", nombre.lower())
        if match_simple:
            nombre_sin_cantidad = match_simple.group(1)
    nombre_busqueda = limpiar_nombre(nombre_sin_cantidad)
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
    variantes = [row[1] for row in rows if row != mas_comun][:4]  # Limitar a máximo 4 sugerencias


    alimento_dict = dict(zip(columns, mas_comun))
    # Detectar cantidad base del alimento en la base
    cantidad_base = None
    for k in alimento_dict:
        if k.lower() in ["cantidad", "peso bruto (g)", "peso neto (g)"]:
            try:
                cantidad_base = float(str(alimento_dict[k]).replace(",",".").split()[0])
                break
            except:
                pass
    if not cantidad_base:
        cantidad_base = 100.0  # Asumir 100g si no hay campo claro

    # Si el usuario pidió una cantidad específica, calcular valores proporcionales
    if cantidad_detectada:
        factor = cantidad_detectada / cantidad_base
    else:
        factor = 1.0

    def escalar(valor):
        try:
            v = float(str(valor).replace(",",".").split()[0])
            return round(v * factor, 2)
        except:
            return valor

    if es_completa:
        alimento_filtrado = {k.title(): escalar(v) if k.lower() not in ["alimento","grupo de alimentos","unidad"] else v for k, v in alimento_dict.items() if k.lower() != "id"}
    else:
        campos_mostrar = {
            "cantidad": "Cantidad",
            "energia (kcal)": "Energía (kcal)",
            "fibra (g)": "Fibra (g)"
        }
        alimento_filtrado = {nuevo: escalar(alimento_dict[original]) for original, nuevo in campos_mostrar.items() if original in alimento_dict}

    # Agregar info de cantidad solicitada si aplica
    if cantidad_detectada:
        alimento_filtrado["Cantidad consultada"] = f"{cantidad_detectada} {unidad_detectada or 'g'}"
        alimento_filtrado["Cantidad base"] = f"{cantidad_base} g"

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

    # Instrucción de sistema profesional para el modelo (simplificada)
    system_instruction = (
        "<|system|>\n"
        "Eres Calyx AI, un asistente inteligente especializado en nutrición, pero también puedes responder preguntas generales siempre que sean apropiadas. "
        "Evita responder con historias personales, experiencias laborales, universidades, anécdotas o cosas inventadas. "
        "Responde siempre en español, de forma breve, clara y profesional. "
        "Si no sabes algo con certeza, admite tu límite con honestidad.\n"
    )
    # Modular el contexto extra según el tipo de pregunta
    if es_nutricion:
        contexto_extra = ("\nSi la pregunta involucra alimentos o nutrición, responde basado en datos reales. "
                          "No inventes datos si no están en la base.\n")
    else:
        contexto_extra = "\nSi es una pregunta general, responde de forma simple y breve.\n"
    prompt_final = f"{system_instruction}{contexto_extra}<|user|>\n{prompt}\n<|assistant|>\n"
    if not ia_engine.is_ready():
        status = ia_engine.get_status()
        print(f"[LOG] /chat error: IA engine not ready: {status['message']}")
        return JSONResponse({"error": status["message"]}, status_code=503 if status["status"]=="loading" else 500)
    try:
        response = ia_engine.generate(prompt_final)
        # Filtrar la respuesta: eliminar líneas que contengan 'Usuario:' o 'Assistant:' y dejar solo la primera línea relevante
        # Filtrar líneas irrelevantes: saludos, profesiones, universidades, etc.
        import re
        lines = [l for l in response.splitlines() if l.strip() and not re.search(r"usuario:|assistant:|profesor|universidad|referencia|finanzas|mercado|analista|complutense|maestr[ií]a|trabajo", l, re.IGNORECASE)]
        # Si hay líneas que no sean saludos genéricos, tomar la primera relevante
        for l in lines:
            if not re.match(r"^(hola|buenas|buenos|qué tal|cómo va|gracias|estoy bien|saludo)", l.strip(), re.IGNORECASE):
                clean_response = l.strip()
                break
        else:
            clean_response = lines[0].strip() if lines else response.strip()
        print(f"[LOG] /chat response: {clean_response}")
        return {"response": clean_response}
    except Exception as e:
        print(f"[LOG] /chat exception: {e}")
        return JSONResponse({"error": f"Ocurrió un error al generar la respuesta: {str(e)}"}, status_code=500)


@app.get("/")
def root():
    return {"message": "Calyx AI backend activo (Phi-3 Mini-4K-Instruct)"}
