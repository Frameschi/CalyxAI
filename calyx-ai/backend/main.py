

from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sqlite3
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
    import unicodedata
    import re
    # --- Limpieza y parsing de nombre y cantidad ---
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

    cantidad_detectada = None
    unidad_detectada = None
    nombre_sin_cantidad = nombre
    match_cant = re.search(r"(\d+(?:[\.,]\d+)?)(\s*)(g|gramos|kg|kilos|ml|l|litros|mg)?\s+de\s+(.+)", nombre.lower())
    if match_cant:
        cantidad_detectada = float(match_cant.group(1).replace(",","."))
        unidad_detectada = match_cant.group(3) or "g"
        nombre_sin_cantidad = match_cant.group(4)
    else:
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
        if a == b:
            return True
        if a in b or b in a:
            return True
        return False

    def get_mas_comun_flexible(rows, nombre_busqueda=None):
        if nombre_busqueda:
            for row in rows:
                if limpiar_nombre(row[1]) == limpiar_nombre(nombre_busqueda):
                    return row
            for row in rows:
                if comparar_flexible(row[1], nombre_busqueda):
                    return row
        return rows[0] if rows else None

    mas_comun = get_mas_comun_flexible(rows, nombre_busqueda)
    variantes = [row[1] for row in rows if row != mas_comun][:4]
    alimento_dict = dict(zip(columns, mas_comun))

    # Detectar cantidad base
    cantidad_base = None
    for k in alimento_dict:
        if k.lower() in ["cantidad", "peso bruto (g)", "peso neto (g)"]:
            try:
                cantidad_base = float(str(alimento_dict[k]).replace(",",".").split()[0])
                break
            except:
                pass
    if not cantidad_base:
        cantidad_base = 100.0
    factor = (cantidad_detectada / cantidad_base) if cantidad_detectada else 1.0

    # --- Selección de campos por categoría ---
    categoria = alimento_dict.get("grupo de alimentos", "").strip().lower()
    campos_por_categoria = {
        "verduras":        ["cantidad", "energia (kcal)", "fibra (g)"],
        "frutas":          ["cantidad", "energia (kcal)", "fibra (g)"],
        "cereales con grasa": ["cantidad", "energia (kcal)", "hidratos de carbono (g)"],
        "cereales sin grasa": ["cantidad", "energia (kcal)", "hidratos de carbono (g)"],
        "leguminosas":     ["cantidad", "energia (kcal)", "proteina (g)"],
        "aoa alto aporte de grasa": ["cantidad", "energia (kcal)", "proteina (g)"],
        "aoa moderado aporte de grasa": ["cantidad", "energia (kcal)", "proteina (g)"],
        "aoa bajo aporte de grasa": ["cantidad", "energia (kcal)", "proteina (g)"],
        "aoa muy bajo aporte de grasa": ["cantidad", "energia (kcal)", "proteina (g)"],
        "leche entera":    ["cantidad", "energia (kcal)", "proteina (g)"],
        "leche semidescremada": ["cantidad", "energia (kcal)", "proteina (g)"],
        "leche descremada": ["cantidad", "energia (kcal)", "proteina (g)"],
        "leche con azúcar": ["cantidad", "energia (kcal)", "proteina (g)"],
        "grasas con proteína": ["cantidad", "energia (kcal)", "lipidos (g)", "proteina (g)"],
        "grasas sin proteína": ["cantidad", "energia (kcal)", "lipidos (g)"],
        "azúcares con grasa": ["cantidad", "energia (kcal)", "hidratos de carbono (g)"],
        "azúcares sin grasa": ["cantidad", "energia (kcal)", "hidratos de carbono (g)"],
        "bebidas alcohólicas": ["cantidad", "energia (kcal)", "etanol (g)"],
        "libres":          ["cantidad", "energia (kcal)", "sodio (mg)"]
    }

    # --- Estructuración profesional de la respuesta ---
    if es_completa:
        # Información nutricional completa como lista de líneas para animación
        info_completa = calcular_info_nutricional_completa(alimento_dict, alimento_dict)
        mensaje = (
            f"Se encontró una coincidencia exacta para '{nombre_busqueda}'."
            if not variantes else
            f"No se encontró una coincidencia exacta para '{nombre_busqueda}'. Mostrando la opción más similar y algunas variantes."
        )
        return {
            "info_completa": info_completa,
            "mensaje": mensaje,
            "sugerencias": variantes
        }
    else:
        # Información básica como filas (clave, valor)
        campos = campos_por_categoria.get(categoria, ["cantidad", "energia (kcal)"])
        info_basica = {}
        for campo in campos:
            if campo in alimento_dict:
                nombre_bonito = campo.replace("(g)", "").replace("(kcal)", "").replace("(mg)", "").replace("de ", "de").title().replace("De ", "de ").replace("Hidratos De Carbono", "Hidratos de Carbono")
                valor = alimento_dict[campo]
                try:
                    v = float(str(valor).replace(",",".").split()[0])
                    valor = round(v * factor, 2)
                except:
                    pass
                info_basica[nombre_bonito] = valor
        unidad = alimento_dict.get("unidad", "g")
        if "Cantidad" in info_basica:
            info_basica = {"Cantidad": info_basica["Cantidad"], "Unidad": unidad, **{k: v for k, v in info_basica.items() if k != "Cantidad"}}
        if cantidad_detectada:
            info_basica["Cantidad consultada"] = f"{cantidad_detectada} {unidad_detectada or 'g'}"
            info_basica["Cantidad base"] = f"{cantidad_base} g"
        filas = calcular_info_nutricional_basica(alimento_dict, info_basica)
        mensaje = (
            f"Se encontró una coincidencia exacta para '{nombre_busqueda}'."
            if not variantes else
            f"No se encontró una coincidencia exacta para '{nombre_busqueda}'. Mostrando la opción más similar y algunas variantes."
        )
        return {
            "filas": filas,
            "mensaje": mensaje,
            "sugerencias": variantes
        }


@app.post("/chat")
async def chat(request: Request):
    print("[LOG] /chat endpoint called")
    data = await request.json()
    print(f"[LOG] /chat received data: {data}")
    prompt = data.get("prompt", "").strip()
    if not prompt:
        print("[LOG] /chat error: No prompt provided")
        return JSONResponse({"error": "No prompt provided"}, status_code=400)

    # --- Lógica para fórmulas: pedir parámetros faltantes ---
    import json
    import re
    # Cargar las fórmulas desde el JSON
    with open("data_formulas.json", encoding="utf-8") as f:
        formulas = json.load(f)

    def detectar_formula_en_prompt(prompt, formulas):
        prompt_l = prompt.lower()
        for key, formula in formulas.items():
            # Buscar por nombre exacto o alias
            nombre = formula.get("nombre", "").lower()
            if nombre and nombre in prompt_l:
                return key, formula
            # Buscar por clave interna
            if key in prompt_l:
                return key, formula
        return None, None

    def extraer_parametros_usuario(prompt, formula):
        params = {}
        for param in formula.get("parametros", []):
            nombre = param["nombre"]
            # Buscar el valor del parámetro en el prompt usando regex simple
            # Ejemplo: "peso 80 kg", "altura 1.75 m", "edad 30 años", "sexo M"
            patron = rf"{nombre}\s*:?\s*([\d\.,]+|[MFmf])"
            m = re.search(patron, prompt, re.IGNORECASE)
            if m:
                valor = m.group(1).replace(",", ".")
                params[nombre] = valor
        return params

    formula_key, formula = detectar_formula_en_prompt(prompt, formulas)
    if formula:
        # Extraer parámetros presentes en el prompt
        params_usuario = extraer_parametros_usuario(prompt, formula)
        # Detectar parámetros faltantes
        faltantes = []
        for param in formula["parametros"]:
            if param["nombre"] not in params_usuario:
                faltantes.append(param)
        if faltantes:
            preguntas = [p["pregunta"] for p in faltantes]
            preguntas_str = " ".join(preguntas)
            return {"response": f"Para calcular la fórmula '{formula['nombre']}' necesito más datos: {preguntas_str}"}
        # Si no faltan parámetros, continuar con el flujo normal (prompt_final)
    # --- Postprocesador para saludos reflejo ---
    def es_solo_salida_reflejo(user_input: str, respuesta: str) -> bool:
        return respuesta.strip().lower() == user_input.strip().lower()

    def respuesta_es_solo_saludo(user_input: str) -> bool:
        texto = user_input.lower()
        return any(f in texto for f in ["hola", "buenas", "¿cómo estás", "como estas", "qué tal", "saludos"])

    SALUDOS_VARIADOS = [
        "¡Hola! ¿En qué puedo ayudarte hoy?",
        "¡Buenas! ¿En qué puedo asistirte?",
        "¡Hola de nuevo! ¿Tienes alguna otra consulta?",
        "¡Aquí estoy! ¿Qué necesitas?",
        "¡Saludos! ¿Cómo puedo ayudarte?",
        "¡Listo para ayudarte! ¿Qué deseas saber?"
    ]
    import random
    def respuesta_para_saludo(user_input: str) -> str:
        if "¿cómo estás" in user_input.lower() or "como estas" in user_input.lower():
            return "¡Hola! Estoy bien, gracias por preguntar. ¿Cómo puedo ayudarte hoy?"
        # Elegir un saludo aleatorio diferente cada vez
        return random.choice(SALUDOS_VARIADOS)

    def postprocesar_respuesta(user_input: str, respuesta: str) -> str:
        if es_solo_salida_reflejo(user_input, respuesta) and respuesta_es_solo_saludo(user_input):
            return respuesta_para_saludo(user_input)
        return respuesta
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

    # Búsqueda flexible: ignorar orden de palabras y acentos
    def normalizar_texto(texto):
        import unicodedata
        texto = texto.lower()
        texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
        palabras = sorted(texto.split())
        return ' '.join(palabras)
    alimento_mencionado = limpiar_nombre(prompt)
    columns, rows = get_alimentos_by_name(alimento_mencionado)
    # 1. Buscar coincidencia exacta (ignorando acentos y mayúsculas)
    def comparar_flexible(a, b):
        a_norm = normalizar_texto(a)
        b_norm = normalizar_texto(b)
        if a_norm == b_norm:
            return True
        if a_norm in b_norm or b_norm in a_norm:
            return True
        return False
    exactos = []
    if rows:
        for row in rows:
            nombre_row = row[columns.index('alimento')] if 'alimento' in columns else row[1]
            if comparar_flexible(nombre_row, alimento_mencionado):
                exactos.append(row)
    # Si hay coincidencia exacta, usar solo esa
    if exactos:
        rows = exactos
    elif rows:
        palabras_clave = set(normalizar_texto(alimento_mencionado).split())
        # Si el alimento solicitado tiene más de una palabra, solo aceptar coincidencias que contengan todas las palabras clave
        if len(palabras_clave) > 1:
            mejores = []
            for row in rows:
                nombre_row = row[columns.index('alimento')] if 'alimento' in columns else row[1]
                palabras_row = set(normalizar_texto(nombre_row).split())
                if palabras_clave.issubset(palabras_row):
                    mejores.append(row)
            if mejores:
                rows = mejores
            else:
                # Si no hay ninguna coincidencia relevante, buscar por similitud semántica
                try:
                    from sentence_transformers import SentenceTransformer, util
                    model = getattr(app.state, "st_model", None)
                    if model is None:
                        model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
                        app.state.st_model = model
                    nombres_alimentos = [row[columns.index('alimento')] if 'alimento' in columns else row[1] for row in rows]
                    emb_consulta = model.encode([alimento_mencionado], convert_to_tensor=True)
                    emb_alimentos = model.encode(nombres_alimentos, convert_to_tensor=True)
                    scores = util.cos_sim(emb_consulta, emb_alimentos)[0].cpu().numpy()
                    idx_max = scores.argmax()
                    if scores[idx_max] > 0.7:
                        rows = [rows[idx_max]]
                    else:
                        return JSONResponse({"error": f"No se encontró información relevante para '{prompt}'"}, status_code=404)
                except Exception as e:
                    return JSONResponse({"error": f"Error en búsqueda semántica: {str(e)}"}, status_code=500)
        else:
            # Si solo es una palabra, usar la mejor por score
            norm_input = normalizar_texto(alimento_mencionado)
            mejor_row = None
            mejor_score = 0
            for row in rows:
                nombre_row = row[columns.index('alimento')] if 'alimento' in columns else row[1]
                score = len(set(norm_input.split()) & set(normalizar_texto(nombre_row).split()))
                if score > mejor_score:
                    mejor_score = score
                    mejor_row = row
            if mejor_row:
                rows = [mejor_row]

    contexto_nutricional = ""
    temas_nutricion = ["alimento", "caloría", "proteína", "fibra", "vitamina", "mineral", "nutrición", "formula", "cálculo", "energía", "macronutriente", "micronutriente"]
    es_nutricion = any(t in prompt.lower() for t in temas_nutricion)

    # Interpolación de datos reales y cálculo proporcional si aplica
    if rows and es_nutricion:
        mas_comun = rows[0]
        alimento_dict = dict(zip(columns, mas_comun))
        nombre_alimento = alimento_dict.get('alimento', alimento_mencionado)
        contexto_nutricional = f"\nInformación nutricional de {nombre_alimento}:\n"
        if "alimento" in alimento_dict:
            contexto_nutricional += f"• Alimento: {nombre_alimento}\n"
        campos_valores = {}
        for campo, etiqueta in [
            ("cantidad", "Cantidad"),
            ("peso bruto (g)", "Cantidad"),
            ("peso neto (g)", "Cantidad"),
            ("energia (kcal)", "Energía"),
            ("calorias", "Energía"),
            ("proteina (g)", "Proteína"),
            ("fibra (g)", "Fibra"),
        ]:
            if campo in alimento_dict:
                contexto_nutricional += f"• {etiqueta}: {alimento_dict[campo]}\n"
                campos_valores[etiqueta] = alimento_dict[campo]
        if "completa" in prompt.lower():
            for k, v in alimento_dict.items():
                if k.lower() != "id" and k.lower() not in ["alimento", "cantidad", "peso bruto (g)", "peso neto (g)", "energia (kcal)", "calorias", "proteina (g)", "fibra (g)"]:
                    contexto_nutricional += f"• {k.title()}: {v}\n"
        import re
        match_cant = re.search(r"(\d+(?:[\.,]\d+)?)(\s*)(g|gramos|kg|kilos|ml|l|litros|mg)?\s+de\s+(.+)", prompt.lower())
        if match_cant:
            cantidad_usuario = float(match_cant.group(1).replace(",","."))
            unidad_usuario = match_cant.group(3) or "g"
            cantidad_base = None
            for k in alimento_dict:
                if k.lower() in ["cantidad", "peso bruto (g)", "peso neto (g)"]:
                    try:
                        cantidad_base = float(str(alimento_dict[k]).replace(",",".").split()[0])
                        break
                    except:
                        pass
            if not cantidad_base:
                cantidad_base = 100.0
            factor = cantidad_usuario / cantidad_base
            energia = None
            proteina = None
            for k in alimento_dict:
                if k.lower() in ["energia (kcal)", "calorias"]:
                    try:
                        energia = round(float(str(alimento_dict[k]).replace(",",".").split()[0]) * factor, 2)
                    except:
                        pass
                if k.lower() == "proteina (g)":
                    try:
                        proteina = round(float(str(alimento_dict[k]).replace(",",".").split()[0]) * factor, 2)
                    except:
                        pass
            contexto_nutricional += f"\nCálculo proporcional para {cantidad_usuario} {unidad_usuario} de {nombre_alimento}:\n"
            if energia is not None:
                contexto_nutricional += f"➡ Energía: {energia} kcal\n"
            if proteina is not None:
                contexto_nutricional += f"➡ Proteína: {proteina} g\n"
        contexto_nutricional += "\nResponde solo usando estos datos. Si falta información, indícalo con honestidad.\n"
    elif es_nutricion:
        contexto_nutricional = "\nResponde solo con información nutricional basada en la base de datos proporcionada. Si no tienes datos, indica que no puedes responder con precisión.\n"
    # Si no es tema de nutrición, no agregar contexto nutricional
    elif es_nutricion:
        contexto_nutricional = "\nResponde solo con información nutricional basada en la base de datos proporcionada. Si no tienes datos, indica que no puedes responder con precisión.\n"
    # Si no es tema de nutrición, no agregar contexto nutricional

    # Instrucción de sistema profesional para el modelo
    system_instruction = (
        "<|system|>\n"
        "Eres Calyx AI, un asistente inteligente especializado en nutrición, pero también puedes responder preguntas generales siempre que sean apropiadas. "
        "Responde exclusivamente sobre el alimento proporcionado. No mezcles ni inventes otros. "
        "Evita responder con historias personales, experiencias laborales, universidades, anécdotas o cosas inventadas. "
        "Responde siempre en español, de forma breve, clara y profesional. "
        "Si no sabes algo con certeza, admite tu límite con honestidad. "
        "Nunca repitas literalmente el mensaje del usuario, ni imites sus palabras o frases. "
        "Si la pregunta es sobre nutrición, responde solo con los datos nutricionales, sin frases introductorias, descripciones generales ni relleno irrelevante.\n"
        f"{contexto_nutricional}"
    )
    # Prompt reforzado para respuestas cerradas y profesionales
    prompt_final = f"{system_instruction}<|user|>\n{prompt}\n<|assistant|>\n"
    if not ia_engine.is_ready():
        status = ia_engine.get_status()
        print(f"[LOG] /chat error: IA engine not ready: {status['message']}")
        return JSONResponse({"error": status["message"]}, status_code=503 if status["status"]=="loading" else 500)
    try:
        # --- Parámetros de generación robustos ---
        gen_args = {
            "max_new_tokens": 180,  # Respuestas completas
            "temperature": 0.6,
            "top_p": 0.9,
        }
        # Si el motor soporta stop tokens, pásalos aquí (simulación si no)
        stop_tokens = ["<|user|>", "<|system|>"]
        # Llamada flexible: si ia_engine.generate acepta kwargs
        import inspect
        sig = inspect.signature(ia_engine.generate)
        if any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values()):
            response = ia_engine.generate(prompt_final, stop=stop_tokens, **gen_args)
        else:
            response = ia_engine.generate(prompt_final)
        # --- Simular stop tokens si el modelo no los soporta ---
        for stop in stop_tokens:
            idx = response.find(stop)
            if idx != -1:
                response = response[:idx]
        # --- Filtrado y postprocesado ---
        import re
        import difflib
        lines = [l for l in response.splitlines() if l.strip() and not re.search(r"usuario:|assistant:|profesor|universidad|referencia|finanzas|mercado|analista|complutense|maestr[ií]a|trabajo", l, re.IGNORECASE)]
        def es_imitacion(linea):
            linea_norm = linea.strip().lower()
            prompt_norm = prompt.strip().lower()
            if linea_norm == prompt_norm:
                return True
            for p in [prompt] + prompt.split('\n'):
                p_norm = p.strip().lower()
                if p_norm and difflib.SequenceMatcher(None, linea_norm, p_norm).ratio() > 0.85:
                    return True
            return False
        # Filtrar eco y repeticiones
        clean_response = None
        for l in lines:
            l_strip = l.strip()
            # No mostrar saludos reflejo, imitaciones, ni repeticiones del prompt
            # Filtrar líneas que repitan instrucciones del system prompt
            instrucciones = [
                "responde exclusivamente sobre el alimento proporcionado",
                "no mezcles ni inventes otros",
                "evita responder con historias personales",
                "experiencias laborales",
                "universidades",
                "anécdotas",
                "cosas inventadas",
                "responde siempre en español",
                "de forma breve, clara y profesional",
                "si no sabes algo con certeza",
                "admite tu límite con honestidad",
                "nunca repitas literalmente el mensaje del usuario",
                "ni imites sus palabras o frases",
                "si la pregunta es sobre nutrición",
                "responde solo con los datos nutricionales",
                "sin frases introductorias",
                "descripciones generales",
                "relleno irrelevante"
            ]
            if (not re.match(r"^(hola|buenas|buenos|qué tal|cómo va|gracias|estoy bien|saludo)", l_strip, re.IGNORECASE)
                and not es_imitacion(l_strip)
                and l_strip.lower() not in ["hola", "hola, buenas tardes", "hola, buenas tardes!", "hola, buenas tardes!!"]
                and l_strip.lower() != prompt.strip().lower()
                and difflib.SequenceMatcher(None, l_strip.lower(), prompt.strip().lower()).ratio() < 0.8
                and not any(instr in l_strip.lower() for instr in instrucciones)):
                # Si es pregunta nutricional, filtrar frases de relleno
                if es_nutricion and re.search(r"(es una|es un|es la|es el|sirve|utilizada|utilizado|perfecta|perfecto|acompañamiento|versátil|fresca|fresco|base sana|preparaciones|ensalada|plato principal|platos más elaborados|picada|picado|junto|otros vegetales|cruda|crudo|hamburguesas|preparaciones saladas|ingredientes para ensalada|ingrediente para ensalada|ingredientes para ensaladas|ingrediente para ensaladas)", l_strip, re.IGNORECASE):
                    continue
                clean_response = l_strip
                break
        if not clean_response:
            clean_response = next((l.strip() for l in lines if l.strip() and l.strip().lower() != prompt.strip().lower()), response.strip())
        # --- Detectar respuesta inconclusa y ofrecer continuar (palabra cortada o frase incompleta) ---
        if re.search(r"[a-záéíóúñ]{3,}$", clean_response) and not re.search(r"[\.\!\?]$", clean_response):
            # Si termina en palabra incompleta o sin puntuación final
            clean_response += " ¿Quieres que continúe la respuesta?"
        # Postprocesar para evitar saludos reflejo
        clean_response = postprocesar_respuesta(prompt, clean_response)
        print(f"[LOG] /chat response: {clean_response}")
        return {"response": clean_response}
    except Exception as e:
        print(f"[LOG] /chat exception: {e}")
        return JSONResponse({"error": f"Ocurrió un error al generar la respuesta: {str(e)}"}, status_code=500)


@app.get("/")
def root():
    return {"message": "Calyx AI backend activo (Phi-3 Mini-4K-Instruct)"}
