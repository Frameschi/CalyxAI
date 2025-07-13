
from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import os
import sqlite3



app = FastAPI()

# Habilitar CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Puedes restringir a ["http://localhost:5173"] si prefieres
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Nombre del modelo en Hugging Face Hub o ruta local
MODEL_NAME = os.getenv("PHI3_MODEL_NAME", "microsoft/phi-3-mini-4k-instruct")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, torch_dtype=torch.float16, device_map="auto")

# Ruta de la base de datos de alimentos
DB_PATH = "datainfo.db"
def get_alimentos_by_name(nombre: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Búsqueda flexible por nombre real de columna
    cursor.execute("SELECT * FROM alimentos WHERE alimento LIKE ?", (f"%{nombre}%",))
    rows = cursor.fetchall()
    # Obtener columnas
    cursor.execute("PRAGMA table_info(alimentos);")
    columns = [col[1] for col in cursor.fetchall()]
    conn.close()
    return columns, rows

def get_mas_comun(rows, nombre_busqueda=None):
    # Prioridad: si hay coincidencia exacta, devolver esa, si no, la primera
    if nombre_busqueda:
        for row in rows:
            if row[1].strip().lower() == nombre_busqueda.strip().lower():
                return row
    return rows[0] if rows else None

@app.get("/alimento")
def buscar_alimento(nombre: str = Query(..., description="Nombre del alimento a buscar")):
    # Detectar si es petición de información completa y extraer el nombre real
    nombre_busqueda = nombre
    es_completa = False
    if "completa" in nombre.lower():
        es_completa = True
        # Extraer el nombre real del alimento
        partes = nombre.lower().split("completa de")
        if len(partes) > 1:
            nombre_busqueda = partes[1].strip()
        else:
            nombre_busqueda = nombre.replace("informacion completa de", "").replace("información completa de", "").strip()

    columns, rows = get_alimentos_by_name(nombre_busqueda)
    if not rows:
        return {"error": f"No se encontró información para '{nombre_busqueda}'"}
    # Buscar el más común (coincidencia exacta si es posible)
    mas_comun = get_mas_comun(rows, nombre_busqueda)
    # Sugerencias de variantes
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
    data = await request.json()
    prompt = data.get("prompt", "")
    if not prompt:
        return JSONResponse({"error": "No prompt provided"}, status_code=400)
    # Tokenizar y generar respuesta
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=128, do_sample=True, temperature=0.7)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return {"response": response}


@app.get("/")
def root():
    return {"message": "Calyx AI backend activo (Phi-3 Mini-4K-Instruct)"}
