

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






# Instancia global del motor de IA - CARGA LAZY
ia_engine = None

def get_ia_engine():
    """Obtiene la instancia global de IAEngine, creándola solo si es necesario"""
    global ia_engine
    if ia_engine is None:
        print("[DEBUG] Inicializando IAEngine por primera vez")
        ia_engine = IAEngine()
    return ia_engine
@app.get("/health")
def health():
    print("[LOG] /health endpoint called")
    return get_ia_engine().get_status()

@app.get("/ping")
async def ping():
    """Endpoint simple para verificar que el servidor funciona sin cargar el modelo"""
    print("[LOG] /ping endpoint called")
    return {"status": "ok", "message": "Server is running", "endpoints": ["ping", "health", "model/status", "chat", "alimento"]}

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
    print("="*50)
    print("[LOG] /chat endpoint called")
    data = await request.json()
    print(f"[LOG] /chat received data: {data}")
    prompt = data.get("prompt", "").strip()
    print(f"[LOG] Prompt extraído: '{prompt}'")
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
        
        # CRÍTICO: Detectar el último mensaje del usuario para nueva solicitud
        # Si hay múltiples líneas, tomar la última solicitud como la intención principal
        lineas = prompt.strip().split('\n')
        ultimo_mensaje = ""
        
        # Buscar el último mensaje del usuario (no ai:)
        for linea in reversed(lineas):
            if linea.strip() and not linea.strip().startswith('ai:'):
                ultimo_mensaje = linea.strip().lower()
                if ultimo_mensaje.startswith('user:'):
                    ultimo_mensaje = ultimo_mensaje[5:].strip()
                break
        
        print(f"[DEBUG] Último mensaje detectado: '{ultimo_mensaje}'")
        
        # FILTRO: Detectar mensajes no relacionados con fórmulas
        mensajes_no_formula_exactos = [
            "hola", "hello", "hi", "gracias", "thank you", "thanks", "grazie", 
            "bye", "adiós", "hasta luego", "ok", "vale", "bien", "perfecto",
            "entendido", "correcto", "sí", "si", "no", "como estas", "cómo estás",
            "que tal", "qué tal", "buenas", "buenos días", "buenas tardes", 
            "buenas noches", "saludo", "despedida", "genial", "excelente", "muy bien",
            "adios", "chao", "nos vemos", "hasta pronto", "que tengas buen día"
        ]
        
        # PATRONES: Detectar mensajes de despedida/agradecimiento con palabras adicionales
        patrones_no_formula = [
            # Patrones de agradecimiento
            r"\b(genial|excelente|perfecto|muy bien|bien)\b.*\b(gracias|thank you)\b",
            r"\b(gracias|thank you)\b.*\b(genial|excelente|perfecto|muy bien|bien)\b",
            # Patrones de despedida AMPLIADOS
            r"\b(buenas noches|hasta luego|adiós|adios|bye|nos vemos|chao|hasta pronto)\b",
            r"\b(seria todo|sería todo|eso es todo|es todo)\b.*\b(adiós|adios|bye|hasta luego|nos vemos|chao)\b",
            r"\b(gracias|thank you)\b.*\b(adiós|adios|bye|hasta luego|nos vemos|chao)\b",
            r"\b(genial|excelente|perfecto)\b.*\b(buenas noches|hasta luego|adiós|adios|bye)\b",
            # Combinaciones de finalización
            r"\b(seria todo|sería todo|eso es todo|es todo|eso seria todo|eso sería todo)\b",
            r"\b(que tengas|que tengan)\b.*\b(buen día|buena tarde|buena noche|buen fin)\b",
            # Combinaciones comunes
            r"\b(genial|excelente|perfecto)\b.*\b(gracias|thank you)\b.*\b(buenas noches|hasta luego|adiós|adios)\b"
        ]
        
        # IMPORTANTE: Aplicar filtro con coincidencia exacta Y patrones
        mensaje_es_simple = False
        
        # 1. Verificar coincidencia exacta
        if ultimo_mensaje and ultimo_mensaje.strip() in mensajes_no_formula_exactos:
            mensaje_es_simple = True
            print(f"[DEBUG] Mensaje simple detectado (exacto): '{ultimo_mensaje}'")
        
        # 2. Verificar patrones con regex
        if not mensaje_es_simple and ultimo_mensaje:
            import re
            for patron in patrones_no_formula:
                if re.search(patron, ultimo_mensaje, re.IGNORECASE):
                    mensaje_es_simple = True
                    print(f"[DEBUG] Mensaje simple detectado (patrón): '{ultimo_mensaje}' -> {patron}")
                    break
        
        # Si es mensaje simple, retornar None para no detectar fórmulas
        if mensaje_es_simple:
            return None, None
        
        # PRIORIDAD ABSOLUTA: Analizar las últimas 5 líneas para detectar nueva solicitud
        lineas_recientes = prompt.strip().split('\n')[-5:]  # Solo últimas 5 líneas
        contexto_reciente = '\n'.join(lineas_recientes).lower()
        
        print(f"[DEBUG] Contexto reciente analizado: {contexto_reciente}")
        
        # PRIMERA PRIORIDAD: Detectar nueva solicitud de IMC en contexto reciente
        solicitudes_imc = [
            "calcular imc", "calcula imc", "imc", "indice de masa corporal", 
            "índice de masa corporal", "calcular mi imc", "calcula mi imc"
        ]
        
        for solicitud in solicitudes_imc:
            if solicitud in contexto_reciente:
                print(f"[DEBUG] Nueva solicitud de IMC detectada en contexto reciente: '{solicitud}'")
                return "imc", formulas.get("imc")
        
        # SEGUNDA PRIORIDAD: Detectar nueva solicitud de composición corporal en contexto reciente
        solicitudes_composicion = [
            "composicion corporal", "composición corporal", "analisis corporal", 
            "análisis corporal", "calcular composicion corporal", "calcular composición corporal",
            "composicion corporal completa", "composición corporal completa",
            "analisis corporal completo", "análisis corporal completo"
        ]
        
        for solicitud in solicitudes_composicion:
            if solicitud in contexto_reciente:
                print(f"[DEBUG] Nueva solicitud de composición corporal detectada en contexto reciente: '{solicitud}'")
                return "composicion_corporal", formulas.get("composicion_corporal")
        
        # FALLBACK: Si NO hay nueva solicitud reciente, analizar por fórmula en progreso
        # Solo usar el contexto histórico si no hay solicitud clara reciente
        
        # IMPORTANTE: PRIORIDAD ABSOLUTA PARA NUEVA SOLICITUD
        # Si detectamos composición corporal en contexto reciente, NO aplicar persistencia de IMC
        
        # Verificar si hay solicitud explícita de composición corporal en las últimas 3 líneas
        lineas_muy_recientes = prompt.strip().split('\n')[-3:]
        contexto_muy_reciente = '\n'.join(lineas_muy_recientes).lower()
        
        # Si hay solicitud de composición corporal muy reciente, ignorar IMC anterior
        if any(sol in contexto_muy_reciente for sol in ["composicion corporal", "composición corporal", "calcular composicion corporal", "calcular composición corporal"]):
            print(f"[DEBUG] COMPOSICIÓN CORPORAL detectada como muy reciente - IGNORANDO persistencia IMC")
            return "composicion_corporal", formulas.get("composicion_corporal")
        
        # Si hay solicitud de IMC muy reciente, aplicar IMC
        if any(sol in contexto_muy_reciente for sol in ["calcular imc", "calcula imc"]):
            print(f"[DEBUG] IMC detectado como muy reciente")
            return "imc", formulas.get("imc")
        
        # PERSISTENCIA LIMITADA: Solo buscar en las últimas 5 líneas para evitar contaminación
        lineas_para_persistencia = prompt.strip().split('\n')[-5:]  # Reducido de 10 a 5
        contexto_persistencia = '\n'.join(lineas_para_persistencia).lower()
        
        # REGLA ESPECÍFICA: Si el último mensaje es un número después de solicitud, mantener fórmula activa
        ultimo_es_numero = re.match(r'^\s*\d+(\.\d+)?\s*$', prompt.strip().split('\n')[-1].strip())
        
        if ultimo_es_numero:
            # Buscar qué fórmula está activa por preguntas específicas en las últimas líneas
            if any(pregunta in contexto_persistencia for pregunta in ["circunferencia media del brazo", "pliegue cutáneo", "tricipital", "cmb", "pct"]):
                print(f"[DEBUG] Número detectado en contexto de composición corporal")
                return "composicion_corporal", formulas.get("composicion_corporal")
            elif any(pregunta in contexto_persistencia for pregunta in ["peso en kg", "altura en metros", "cuál es tu peso", "cuál es tu altura"]):
                print(f"[DEBUG] Número detectado en contexto de IMC")
                return "imc", formulas.get("imc")
        
        # Detectar composición corporal por preguntas específicas SOLO si no hay solicitud IMC reciente
        preguntas_composicion = [
            "circunferencia media del brazo", "pliegue cutáneo", "tricipital", 
            "bicipital", "subescapular", "ilíaco", "cmb", "pct", "pcb", "pcse", "pci"
        ]
        
        hay_preguntas_composicion = any(pregunta in prompt_l for pregunta in preguntas_composicion)
        
        # COMPOSICIÓN CORPORAL: Detectar por preguntas específicas o solicitud explícita  
        if (hay_preguntas_composicion or 
            "composicion corporal" in prompt_l or 
            "composición corporal" in prompt_l):
            print(f"[DEBUG] Composición corporal detectada por contenido")
            return "composicion_corporal", formulas.get("composicion_corporal")
        
        # Detectar IMC por contexto general (mantenido para compatibilidad)
        if any(solicitud in prompt_l for solicitud in [
            "calcular imc", "calcula imc", "imc", "indice de masa corporal", 
            "índice de masa corporal", "calcular mi imc", "calcula mi imc"
        ]):
            print(f"[DEBUG] IMC detectado en progreso")
            return "imc", formulas.get("imc")
        
        # Buscar por términos mapeados como último recurso
        mapeo_terminos = {
            "imc": "imc",
            "indice de masa corporal": "imc",
            "índice de masa corporal": "imc",
            "composicion corporal": "composicion_corporal",
            "composición corporal": "composicion_corporal", 
            "composicion corporal completa": "composicion_corporal",
            "composición corporal completa": "composicion_corporal",
            "calcular composicion corporal": "composicion_corporal",
            "calcular composición corporal": "composicion_corporal",
            "analisis corporal": "composicion_corporal",
            "análisis corporal": "composicion_corporal",
            "analisis corporal completo": "composicion_corporal",
            "análisis corporal completo": "composicion_corporal",
            "grasa corporal": "composicion_corporal",
            "masa corporal": "composicion_corporal",
            "densidad corporal": "composicion_corporal"
        }
        
        for termino, clave in mapeo_terminos.items():
            if termino in prompt_l and clave in formulas:
                return clave, formulas[clave]
        
        # Buscar por nombre exacto o clave
        for key, formula in formulas.items():
            # Buscar por nombre exacto o alias
            nombre = formula.get("nombre", "").lower()
            if nombre and nombre in prompt_l:
                return key, formula
            # Buscar por clave interna
            if key in prompt_l:
                return key, formula
        return None, None

    def extraer_parametros_usuario(prompt, formula, es_nueva_solicitud=False):
        params = {}
        
        # CRÍTICO: Si es una nueva solicitud, SOLO buscar después de la solicitud explícita
        # NO mezclar parámetros de conversaciones anteriores de otras fórmulas
        if es_nueva_solicitud:
            print(f"[DEBUG] NUEVA SOLICITUD - Buscando parámetros SOLO después de la solicitud explícita")
            
            # Encontrar dónde empezó la nueva solicitud
            lineas = prompt.strip().split('\n')
            inicio_nueva_solicitud = -1
            
            # Buscar la línea que contiene la nueva solicitud
            solicitudes_formulas = [
                "calcular imc", "calcula imc", "imc", 
                "composicion corporal", "composición corporal", "analisis corporal", "análisis corporal",
                "calcular composicion corporal", "calcular composición corporal"
            ]
            
            for i, linea in enumerate(lineas):
                linea_lower = linea.lower()
                for solicitud in solicitudes_formulas:
                    if solicitud in linea_lower:
                        # Verificar que coincida con la fórmula actual
                        es_solicitud_imc = any(s in solicitud for s in ["imc", "indice", "índice"])
                        es_solicitud_comp = any(s in solicitud for s in ["composicion", "composición", "analisis", "análisis"])
                        formula_es_imc = formula.get("nombre", "").lower() == "imc"
                        formula_es_comp = "composicion" in formula.get("nombre", "").lower()
                        
                        if (es_solicitud_imc and formula_es_imc) or (es_solicitud_comp and formula_es_comp):
                            inicio_nueva_solicitud = i
                            print(f"[DEBUG] Nueva solicitud encontrada en línea {i}: '{linea.strip()}'")
                            break
                
                if inicio_nueva_solicitud != -1:
                    break
            
            # Solo buscar parámetros DESPUÉS de la nueva solicitud
            if inicio_nueva_solicitud != -1:
                lineas_relevantes = lineas[inicio_nueva_solicitud:]
                texto = '\n'.join(lineas_relevantes).lower()
                print(f"[DEBUG] Analizando SOLO contexto después de nueva solicitud: {len(lineas_relevantes)} líneas")
            else:
                # Si no encontramos la solicitud, usar solo las últimas 3 líneas
                texto = '\n'.join(lineas[-3:]).lower()
                print(f"[DEBUG] No se encontró solicitud explícita, usando últimas 3 líneas")
        else:
            # RECOLECCIÓN PROGRESIVA: Buscar en contexto de la fórmula actual
            print(f"[DEBUG] Recolección progresiva - buscando parámetros de fórmula en progreso")
            
            # CRÍTICO: Para recolección progresiva, buscar en TODO el contexto 
            # para NO perder parámetros de conversaciones largas como composición corporal
            lineas = prompt.strip().split('\n')
            texto = '\n'.join(lineas).lower()
            print(f"[DEBUG] Analizando TODAS las {len(lineas)} líneas para recolección progresiva completa")
        
        # 1. Peso (kg) - buscar TODOS los valores de peso mencionados
        patrones_peso = [
            r'(\d{1,3}(?:[\.,]\d+)?)\s*(?:kg|kilogramos?|kilos?)',
            r'peso.*?(\d{1,3}(?:[\.,]\d+)?)',
            r'¿cuál es tu peso.*?(\d{1,3}(?:[\.,]\d+)?)'
        ]
        
        for patron in patrones_peso:
            matches = re.findall(patron, texto, re.IGNORECASE | re.DOTALL)
            for match in matches:
                valor = float(match.replace(",", "."))
                if 30 <= valor <= 200:  # Rango válido para peso
                    params["peso"] = str(valor)
                    print(f"[DEBUG] Peso encontrado: {valor}")
                    break
            if "peso" in params:
                break
        
        # 2. Altura (metros o cm) - buscar TODOS los valores de altura mencionados
        patrones_altura = [
            r'(\d{1,2}[\.,]\d{1,2})\s*(?:m|metros?)',
            r'(\d{2,3})\s*(?:cm|centimetros?|centímetros?)',
            r'altura.*?(\d{1,2}[\.,]\d{1,2})',
            r'¿cuál es tu altura.*?(\d{1,2}[\.,]\d{1,2})',
            r'¿cuál es tu altura.*?(\d{2,3})'
        ]
        
        for patron in patrones_altura:
            matches = re.findall(patron, texto, re.IGNORECASE | re.DOTALL)
            for match in matches:
                valor = float(match.replace(",", "."))
                if 1.0 <= valor <= 2.5:  # Metros
                    params["altura"] = str(valor)
                    print(f"[DEBUG] Altura encontrada en metros: {valor}")
                    break
                elif 140 <= valor <= 220:  # Centímetros
                    params["altura"] = str(valor / 100)
                    print(f"[DEBUG] Altura encontrada en cm: {valor} -> {valor/100}m")
                    break
            if "altura" in params:
                break
        
        # 3. Edad (años) - buscar TODOS los valores de edad mencionados
        patrones_edad = [
            r'(\d{1,3})\s*años?',
            r'edad.*?(\d{1,3})',
            r'¿cuántos años.*?(\d{1,3})',
            r'tienes.*?(\d{1,3})'
        ]
        
        for patron in patrones_edad:
            matches = re.findall(patron, texto, re.IGNORECASE | re.DOTALL)
            for match in matches:
                valor = int(match)
                if 10 <= valor <= 120:  # Rango válido para edad
                    params["edad"] = str(valor)
                    print(f"[DEBUG] Edad encontrada: {valor}")
                    break
            if "edad" in params:
                break
        
        # 4. Sexo (M/F) - buscar TODOS los valores de sexo mencionados
        patrones_sexo = [
            r'\b([MFmf])\b',
            r'sexo.*?([MFmf])',
            r'masculino|femenino|hombre|mujer'
        ]
        
        for patron in patrones_sexo:
            matches = re.findall(patron, texto, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if isinstance(match, str) and len(match) == 1:
                    params["sexo"] = match.upper()
                    print(f"[DEBUG] Sexo encontrado: {match.upper()}")
                    break
                elif "masculino" in match.lower() or "hombre" in match.lower():
                    params["sexo"] = "M"
                    print(f"[DEBUG] Sexo encontrado: M")
                    break
                elif "femenino" in match.lower() or "mujer" in match.lower():
                    params["sexo"] = "F"
                    print(f"[DEBUG] Sexo encontrado: F")
                    break
            if "sexo" in params:
                break
        
        # 5. Circunferencia media del brazo (cm)
        patrones_cmb = [
            r'(\d{1,3}(?:[\.,]\d+)?)\s*cm.*?brazo',
            r'brazo.*?(\d{1,3}(?:[\.,]\d+)?)\s*cm',
            r'circunferencia.*?brazo.*?(\d{1,3}(?:[\.,]\d+)?)',
            r'cmb.*?(\d{1,3}(?:[\.,]\d+)?)'
        ]
        
        for patron in patrones_cmb:
            matches = re.findall(patron, texto, re.IGNORECASE | re.DOTALL)
            for match in matches:
                valor = float(match.replace(",", "."))
                if 15 <= valor <= 50:  # Rango válido para CMB
                    params["cmb"] = str(valor)
                    print(f"[DEBUG] CMB encontrado: {valor}")
                    break
            if "cmb" in params:
                break
        
        # 6. Pliegues cutáneos (mm)
        pliegues_patrones = {
            "pct": [r'tricipital.*?(\d{1,2}(?:[\.,]\d+)?)', r'pct.*?(\d{1,2}(?:[\.,]\d+)?)'],
            "pcb": [r'bicipital.*?(\d{1,2}(?:[\.,]\d+)?)', r'pcb.*?(\d{1,2}(?:[\.,]\d+)?)'],
            "pcse": [r'subescapular.*?(\d{1,2}(?:[\.,]\d+)?)', r'pcse.*?(\d{1,2}(?:[\.,]\d+)?)'],
            "pci": [r'ilíaco.*?(\d{1,2}(?:[\.,]\d+)?)', r'iliaco.*?(\d{1,2}(?:[\.,]\d+)?)', r'pci.*?(\d{1,2}(?:[\.,]\d+)?)']
        }
        
        for pliegue, patrones in pliegues_patrones.items():
            for patron in patrones:
                matches = re.findall(patron, texto, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    valor = float(match.replace(",", "."))
                    if 3 <= valor <= 50:  # Rango válido para pliegues
                        params[pliegue] = str(valor)
                        print(f"[DEBUG] {pliegue.upper()} encontrado: {valor}")
                        break
                if pliegue in params:
                    break
        
        # FALLBACK: Si no se encontraron valores específicos, buscar números sueltos
        if len(params) == 0:
            print(f"[DEBUG] No se encontraron parámetros específicos, usando fallback")
            # Solo buscar números cerca de preguntas específicas
            lineas = texto.split('\n')
            for i, linea in enumerate(lineas):
                linea = linea.strip().lower()
                if "peso" in linea and i + 1 < len(lineas):
                    siguiente = lineas[i + 1].strip()
                    numeros = re.findall(r'(\d{1,3}(?:[\.,]\d+)?)', siguiente)
                    for num in numeros:
                        valor = float(num.replace(",", "."))
                        if 30 <= valor <= 200:
                            params["peso"] = str(valor)
                            break
                
                elif "altura" in linea and i + 1 < len(lineas):
                    siguiente = lineas[i + 1].strip()
                    numeros = re.findall(r'(\d{1,3}(?:[\.,]\d+)?)', siguiente)
                    for num in numeros:
                        valor = float(num.replace(",", "."))
                        if 1.0 <= valor <= 2.5:
                            params["altura"] = str(valor)
                            break
                        elif 140 <= valor <= 220:
                            params["altura"] = str(valor / 100)
                            break
                
                elif "años" in linea and i + 1 < len(lineas):
                    siguiente = lineas[i + 1].strip()
                    numeros = re.findall(r'(\d{1,3})', siguiente)
                    for num in numeros:
                        valor = int(num)
                        if 10 <= valor <= 120:
                            params["edad"] = str(valor)
                            break
                
                elif "sexo" in linea and i + 1 < len(lineas):
                    siguiente = lineas[i + 1].strip()
                    match = re.search(r'\b([MFmf])\b', siguiente)
                    if match:
                        params["sexo"] = match.group(1).upper()
                        break
        
        print(f"[DEBUG] Parámetros finales extraídos: {params}")
        return params

    formula_key, formula = detectar_formula_en_prompt(prompt, formulas)
    
    print(f"[DEBUG CRÍTICO] Formula detectada: {formula_key}")
    print(f"[DEBUG CRÍTICO] Formula objeto: {formula.get('nombre') if formula else 'None'}")
    
    # *** CRÍTICO: PRIORIDAD ABSOLUTA PARA MENSAJES SIMPLES ***
    # Si detectar_formula_en_prompt retorna None, None significa mensaje no relacionado
    # FORZAR respuesta inmediata sin continuar con lógica de fórmulas
    if formula_key is None and formula is None:
        lineas = prompt.strip().split('\n')
        ultimo_mensaje = ""
        for linea in reversed(lineas):
            if linea.strip() and not linea.strip().startswith('ai:'):
                ultimo_mensaje = linea.strip().lower()
                if ultimo_mensaje.startswith('user:'):
                    ultimo_mensaje = ultimo_mensaje[5:].strip()
                break

        print(f"[DEBUG] MENSAJE SIMPLE DETECTADO - RETORNANDO INMEDIATAMENTE: '{ultimo_mensaje}'")
        
        # Determinar tipo de respuesta
        if re.search(r"\b(hola|hello|hi|buenas|buenos días|buenas tardes)\b", ultimo_mensaje, re.IGNORECASE):
            return {"message": "¡Hola! Soy CalyxAI, tu asistente nutricional. ¿En qué puedo ayudarte hoy? Puedo buscar información nutricional de alimentos o calcular tu IMC.", "console_block": None}
        elif re.search(r"\b(gracias|thank you|thanks|genial|excelente|perfecto|muy bien)\b", ultimo_mensaje, re.IGNORECASE):
            return {"message": "¡De nada! ¿Hay algo más en lo que pueda ayudarte?", "console_block": None}
        elif re.search(r"\b(adiós|adios|bye|hasta luego|nos vemos|chao|hasta pronto|buenas noches|seria todo|sería todo|es todo)\b", ultimo_mensaje, re.IGNORECASE):
            return {"message": "¡Hasta luego! Que tengas un excelente día. Estoy aquí cuando necesites ayuda nutricional.", "console_block": None}
        else:
            return {"message": "¡Hola! ¿En qué puedo ayudarte hoy? Puedo calcular tu IMC o buscar información nutricional.", "console_block": None}
    
    # *** SOLO CONTINUAR SI HAY FÓRMULA DETECTADA ***
    if not formula:
        # Si no hay fórmula, usar fallback de IA general
        try:
            ia_engine = get_ia_engine()
            if ia_engine is None:
                return {"message": "Lo siento, no puedo procesar tu solicitud en este momento. ¿Puedes intentar calcular tu IMC?", "console_block": None}
            
            response = ia_engine.generate(prompt, max_new_tokens=150, temperature=0.3)
            return {"message": response, "console_block": None}
        except Exception as e:
            return {"message": "¿En qué puedo ayudarte? Puedo calcular tu IMC o buscar información nutricional.", "console_block": None}
    
    # *** SOLO LLEGAR AQUÍ SI HAY FÓRMULA VÁLIDA ***
    if formula:
        # CRÍTICO: Detectar si es una nueva solicitud de fórmula
        # Si el último mensaje del usuario contiene una nueva solicitud, limpiar contexto
        lineas = prompt.strip().split('\n')
        ultimo_mensaje = ""
        
        # Buscar el último mensaje del usuario
        for linea in reversed(lineas):
            if linea.strip() and not linea.strip().startswith('ai:'):
                ultimo_mensaje = linea.strip().lower()
                if ultimo_mensaje.startswith('user:'):
                    ultimo_mensaje = ultimo_mensaje[5:].strip()
                break
        
        # Determinar si es una nueva solicitud de fórmula
        es_nueva_solicitud = False
        if ultimo_mensaje:
            # SOLO considerar nueva solicitud si es una palabra clave específica de fórmula
            # NO si es un número o respuesta a pregunta
            
            # Primero verificar si es solo un número o respuesta simple
            es_respuesta_numero = re.match(r'^\s*\d+(\.\d+)?\s*$', ultimo_mensaje.strip())
            es_respuesta_sexo = re.match(r'^\s*[mf]\s*$', ultimo_mensaje.strip(), re.IGNORECASE)
            es_respuesta_simple = es_respuesta_numero or es_respuesta_sexo
            
            if not es_respuesta_simple:
                # Solo entonces verificar si es nueva solicitud de fórmula
                nuevas_solicitudes = [
                    # Composición corporal
                    "composicion corporal", "composición corporal", "analisis corporal", 
                    "análisis corporal", "calcular composicion corporal", "calcular composición corporal",
                    "composicion corporal completa", "composición corporal completa",
                    # IMC
                    "calcular imc", "calcula imc", "imc", "indice de masa corporal", 
                    "índice de masa corporal", "calcular mi imc", "calcula mi imc",
                    # TMB
                    "tmb", "calcular tmb", "tasa metabolica basal", "tasa metabólica basal",
                    "harris benedict", "harris-benedict",
                    # Otros
                    "agua corporal", "calcular agua", "requerimiento proteico", "proteina"
                ]
                for solicitud in nuevas_solicitudes:
                    if solicitud in ultimo_mensaje:
                        es_nueva_solicitud = True
                        print(f"[DEBUG] Nueva solicitud detectada: {solicitud}")
                        
                        # CRÍTICO: Verificar si es diferente fórmula
                        solicitud_es_imc = any(s in solicitud for s in ["imc", "indice", "índice"])
                        solicitud_es_composicion = any(s in solicitud for s in ["composicion", "composición", "analisis", "análisis"])
                        formula_actual_es_imc = formula_key == "imc"
                        formula_actual_es_composicion = formula_key == "composicion_corporal"
                        
                        # Si solicita IMC pero la fórmula actual es composición, o viceversa
                        if (solicitud_es_imc and not formula_actual_es_imc) or \
                           (solicitud_es_composicion and not formula_actual_es_composicion):
                            print(f"[DEBUG] CAMBIO DE FÓRMULA detectado: {solicitud} -> {formula_key}")
                            es_nueva_solicitud = True
                        
                        # FORZAR nueva solicitud si es una solicitud explícita de fórmula
                        if solicitud in ultimo_mensaje:
                            print(f"[DEBUG] SOLICITUD EXPLÍCITA detectada - FORZANDO nueva solicitud")
                            es_nueva_solicitud = True
                        
                        break
        
        # CRÍTICO: Extraer parámetros considerando si es nueva solicitud
        # Si es nueva solicitud, solo buscar en contexto reciente
        # Si no, buscar en toda la conversación para recolección progresiva
        params_usuario = extraer_parametros_usuario(prompt, formula, es_nueva_solicitud)
        
        # DEBUG: Log para verificar qué parámetros se están extrayendo
        print(f"[DEBUG] Parámetros extraídos: {params_usuario}")
        print(f"[DEBUG] Es nueva solicitud: {es_nueva_solicitud}")
        print(f"[DEBUG] Fórmula detectada: {formula_key}")
        
        # CRÍTICO: Si es nueva solicitud, mantener la fórmula activa sin volver a detectar
        # Esto evita que el sistema cambie de fórmula cuando el usuario responde con datos
        if es_nueva_solicitud:
            # Marcar que tenemos una fórmula activa persistente
            formula_activa = formula_key
            print(f"[DEBUG] Fórmula activa establecida: {formula_activa}")
        else:
            # Si no es nueva solicitud, verificar si hay fórmula activa en el contexto reciente
            lineas_recientes = prompt.strip().split('\n')[-10:]
            contexto_reciente = '\n'.join(lineas_recientes).lower()
            
            # IMPORTANTE: Solo aplicar persistencia si NO HAY nueva solicitud explícita diferente
            # Si hay "calcular imc" en las últimas líneas Y no hay solicitud de composición corporal reciente
            tiene_imc_reciente = any(sol in contexto_reciente for sol in ["calcular imc", "calcula imc"])
            tiene_composicion_reciente = any(sol in contexto_reciente for sol in ["composicion corporal", "composición corporal", "analisis corporal", "análisis corporal"])
            
            if tiene_imc_reciente and not tiene_composicion_reciente and formula_key != "imc":
                print(f"[DEBUG] Manteniendo IMC activo por solicitud reciente (sin interferencia de composición)")
                formula_key = "imc"
                formula = formulas.get("imc")
            elif tiene_composicion_reciente and not tiene_imc_reciente and formula_key != "composicion_corporal":
                print(f"[DEBUG] Manteniendo composición corporal activa por solicitud reciente (sin interferencia de IMC)")
                formula_key = "composicion_corporal"
                formula = formulas.get("composicion_corporal")
        
        # Detectar parámetros faltantes
        faltantes = []
        for param in formula["parametros"]:
            if param["nombre"] not in params_usuario:
                faltantes.append(param)
        
        print(f"[DEBUG] Parámetros faltantes: {[p['nombre'] for p in faltantes]}")
        
        if faltantes:
            # Sistema de preguntas progresivas - una pregunta a la vez
            primer_faltante = faltantes[0]
            pregunta_individual = primer_faltante["pregunta"]
            
            # Hacer la pregunta más amigable según el parámetro
            if primer_faltante["nombre"] == "peso":
                pregunta_individual = "¿Cuál es tu peso en kg?"
            elif primer_faltante["nombre"] == "altura":
                pregunta_individual = "¿Cuál es tu altura en metros? (ejemplo: 1.75)"
            elif primer_faltante["nombre"] == "edad":
                pregunta_individual = "¿Cuántos años tienes?"
            elif primer_faltante["nombre"] == "sexo":
                pregunta_individual = "¿Cuál es tu sexo? (M para masculino, F para femenino)"
            elif primer_faltante["nombre"] == "cmb":
                pregunta_individual = "¿Cuál es tu circunferencia media del brazo en cm? (medida alrededor del punto medio del brazo)"
            elif primer_faltante["nombre"] == "pct":
                pregunta_individual = "¿Cuál es tu pliegue cutáneo tricipital en mm? (pellizco en la parte posterior del brazo)"
            elif primer_faltante["nombre"] == "pcb":
                pregunta_individual = "¿Cuál es tu pliegue cutáneo bicipital en mm? (pellizco en la parte frontal del brazo)"
            elif primer_faltante["nombre"] == "pcse":
                pregunta_individual = "¿Cuál es tu pliegue cutáneo subescapular en mm? (pellizco debajo del omóplato)"
            elif primer_faltante["nombre"] == "pci":
                pregunta_individual = "¿Cuál es tu pliegue cutáneo ilíaco en mm? (pellizco en la cresta ilíaca/cadera)"
            
            return {"message": pregunta_individual, "console_block": None}
        # Si no faltan parámetros, realizar el cálculo según la fórmula
        if formula_key.lower() == "imc":
            try:
                peso = float(params_usuario.get("peso"))
                altura = float(params_usuario.get("altura"))
                if altura <= 0:
                    return {
                        "message": "Error: La altura debe ser mayor a cero.",
                        "console_block": {
                            "title": "Cálculo del IMC",
                            "input": "Peso: -- kg\nAltura: -- m",
                            "output": "FÓRMULA:\nIMC = peso / altura²\n\nSUSTITUCIÓN:\n-\n\nRESULTADO:\nError: La altura debe ser mayor a cero."
                        }
                    }
                imc = round(peso / (altura ** 2), 2)
                # Interpretación desde la tabla
                interpretacion = ""
                for rango in formula.get("interpretacion", []):
                    if imc >= rango["min"] and imc <= rango["max"]:
                        interpretacion = rango["texto"]
                        break
                output_block = (
                    f"> Cálculo del IMC\n\n"
                    f"DATOS DE ENTRADA:\nPeso: {peso} kg\nAltura: {altura} m\n\n"
                    "FÓRMULA:\nIMC = peso / altura²\n\n"
                    f"SUSTITUCIÓN:\nIMC = {peso} / ({altura})^2\n\n"
                    f"RESULTADO:\nIMC = {imc} ({interpretacion})"
                )
                return {
                    "message": "",
                    "console_block": {
                        "title": "Cálculo",
                        "input": "",
                        "output": output_block
                    }
                }
            except Exception as e:
                return {
                    "message": f"Error al calcular el IMC: {str(e)}",
                    "console_block": {
                        "title": "Cálculo del IMC",
                        "input": "-",
                        "output": f"RESULTADO:\nError al calcular el IMC: {str(e)}"
                    }
                }
        elif formula_key.lower() == "composicion_corporal":
            print(f"[DEBUG COMPOSICIÓN] Iniciando cálculo de composición corporal")
            print(f"[DEBUG COMPOSICIÓN] Parámetros recibidos: {params_usuario}")
            try:
                peso = float(params_usuario.get("peso"))
                altura = float(params_usuario.get("altura"))
                edad = int(params_usuario.get("edad"))
                sexo = params_usuario.get("sexo", "").upper()
                cmb = float(params_usuario.get("cmb"))  # Circunferencia Media del Brazo (cm)
                pct_mm = float(params_usuario.get("pct"))  # Pliegue Cutáneo Tricipital (mm)
                pcb_mm = float(params_usuario.get("pcb"))  # Pliegue Cutáneo Bicipital (mm)
                pcse_mm = float(params_usuario.get("pcse"))  # Pliegue Cutáneo Subescapular (mm)
                pci_mm = float(params_usuario.get("pci"))  # Pliegue Cutáneo Ilíaco (mm)
                
                print(f"[DEBUG COMPOSICIÓN] Parámetros parseados correctamente:")
                print(f"  peso={peso}, altura={altura}, edad={edad}, sexo={sexo}")
                print(f"  cmb={cmb}, pct={pct_mm}, pcb={pcb_mm}, pcse={pcse_mm}, pci={pci_mm}")
                
                if altura <= 0 or cmb <= 0 or pct_mm <= 0 or pcb_mm <= 0 or pcse_mm <= 0 or pci_mm <= 0:
                    print(f"[DEBUG COMPOSICIÓN] Error: valores <= 0 detectados")
                    return {
                        "message": "Error: Todos los valores deben ser mayores a cero.",
                        "console_block": {
                            "title": "Composición Corporal",
                            "input": "Error en los datos",
                            "output": "RESULTADO:\nError: Todos los valores deben ser mayores a cero."
                        }
                    }
                
                import math
                
                # 1. ÁREA MUSCULAR BRAQUIAL DISPONIBLE (AMBd)
                # Convertir PCT de mm a cm para la fórmula
                pct_cm = pct_mm / 10
                
                # Fórmula: AMBd = [CMB - (π × PCT cm)]² / (4 × π) - constante
                # Constante: -10 para hombres, -6.5 para mujeres
                constante = -10 if sexo == "M" else -6.5
                
                # Calcular área muscular braquial
                numerador = (cmb - (math.pi * pct_cm)) ** 2
                denominador = 4 * math.pi
                ambd = round((numerador / denominador) + constante, 2)
                
                # Interpretación del AMBd (como porcentaje de referencia)
                # Para simplicidad, asumiremos valores de referencia estándar
                # TODO: Implementar tabla de referencia real según sexo y edad
                ambd_referencia = 50 if sexo == "M" else 35  # Valores aproximados de referencia
                porcentaje_ambd = round((ambd / ambd_referencia) * 100, 1)
                
                interpretacion_ambd = ""
                for rango in formula.get("interpretacion", []):
                    if rango.get("parametro") == "ambd" and porcentaje_ambd >= rango["min"] and porcentaje_ambd <= rango["max"]:
                        interpretacion_ambd = rango["texto"]
                        break
                
                if not interpretacion_ambd:
                    if porcentaje_ambd >= 80:
                        interpretacion_ambd = "Área muscular normal"
                    elif porcentaje_ambd >= 60:
                        interpretacion_ambd = "Deficiencia leve"
                    elif porcentaje_ambd >= 40:
                        interpretacion_ambd = "Deficiencia moderada"
                    else:
                        interpretacion_ambd = "Deficiencia severa"
                
                # 2. MASA MUSCULAR TOTAL (MMT)
                # Fórmula: MMT = Talla (cm) × [(0.0264) + (0.0029 × AMBd)]
                # Convertir altura de metros a centímetros
                altura_cm = altura * 100
                
                # Calcular masa muscular total
                factor_1 = 0.0264
                factor_2 = 0.0029 * ambd
                mmt = round(altura_cm * (factor_1 + factor_2), 2)
                
                # Interpretación de la masa muscular total
                interpretacion_mmt = ""
                for rango in formula.get("interpretacion", []):
                    if rango.get("parametro") == "mmt" and mmt >= rango["min"] and mmt <= rango["max"]:
                        interpretacion_mmt = rango["texto"]
                        break
                
                if not interpretacion_mmt:
                    if mmt >= 25:
                        interpretacion_mmt = "Masa muscular total normal"
                    elif mmt >= 20:
                        interpretacion_mmt = "Masa muscular baja"
                    else:
                        interpretacion_mmt = "Masa muscular muy baja"
                
                # 3. DENSIDAD CORPORAL (D)
                # Fórmula: D = c - [m × logaritmo de suma de pliegues]
                # Suma de los 4 pliegues cutáneos
                suma_pliegues = pct_mm + pcb_mm + pcse_mm + pci_mm
                
                # Constantes según sexo (valores estándar de Durnin-Womersley)
                if sexo == "M":  # Hombres
                    c = 1.1765
                    m = 0.0744
                else:  # Mujeres
                    c = 1.1567
                    m = 0.0717
                
                # Calcular densidad corporal
                import math
                densidad = round(c - (m * math.log10(suma_pliegues)), 4)
                
                # Interpretación de la densidad corporal
                interpretacion_densidad = ""
                for rango in formula.get("interpretacion", []):
                    if rango.get("parametro") == "densidad" and densidad >= rango["min"] and densidad <= rango["max"]:
                        interpretacion_densidad = rango["texto"]
                        break
                
                if not interpretacion_densidad:
                    if densidad >= 1.050:
                        interpretacion_densidad = "Densidad corporal normal"
                    elif densidad >= 1.030:
                        interpretacion_densidad = "Densidad corporal baja"
                    else:
                        interpretacion_densidad = "Densidad corporal muy baja"
                
                # 4. PORCENTAJE DE GRASA CORPORAL
                # Fórmula: % Grasa = (4.95/Densidad - 4.5) × 100
                porcentaje_grasa = round((4.95/densidad - 4.5) * 100, 1)
                
                # Interpretación del porcentaje de grasa según sexo y edad (NIH/OMS)
                interpretacion_grasa = ""
                
                if sexo == "M":  # Hombre
                    if 20 <= edad <= 39:
                        if porcentaje_grasa < 8:
                            interpretacion_grasa = "Bajo/Magro"
                        elif 8 <= porcentaje_grasa <= 19.9:
                            interpretacion_grasa = "Normal/Saludable"
                        elif 20 <= porcentaje_grasa <= 24.9:
                            interpretacion_grasa = "Alto/Sobrepeso"
                        else:
                            interpretacion_grasa = "Muy Alto/Obesidad"
                    elif 40 <= edad <= 59:
                        if porcentaje_grasa < 11:
                            interpretacion_grasa = "Bajo/Magro"
                        elif 11 <= porcentaje_grasa <= 21.9:
                            interpretacion_grasa = "Normal/Saludable"
                        elif 22 <= porcentaje_grasa <= 27.9:
                            interpretacion_grasa = "Alto/Sobrepeso"
                        else:
                            interpretacion_grasa = "Muy Alto/Obesidad"
                    elif 60 <= edad <= 79:
                        if porcentaje_grasa < 13:
                            interpretacion_grasa = "Bajo/Magro"
                        elif 13 <= porcentaje_grasa <= 24.9:
                            interpretacion_grasa = "Normal/Saludable"
                        elif 25 <= porcentaje_grasa <= 29.9:
                            interpretacion_grasa = "Alto/Sobrepeso"
                        else:
                            interpretacion_grasa = "Muy Alto/Obesidad"
                else:  # Mujer
                    if 20 <= edad <= 39:
                        if porcentaje_grasa < 21:
                            interpretacion_grasa = "Bajo/Magro"
                        elif 21 <= porcentaje_grasa <= 32.9:
                            interpretacion_grasa = "Normal/Saludable"
                        elif 33 <= porcentaje_grasa <= 38.9:
                            interpretacion_grasa = "Alto/Sobrepeso"
                        else:
                            interpretacion_grasa = "Muy Alto/Obesidad"
                    elif 40 <= edad <= 59:
                        if porcentaje_grasa < 23:
                            interpretacion_grasa = "Bajo/Magro"
                        elif 23 <= porcentaje_grasa <= 33.9:
                            interpretacion_grasa = "Normal/Saludable"
                        elif 34 <= porcentaje_grasa <= 39.9:
                            interpretacion_grasa = "Alto/Sobrepeso"
                        else:
                            interpretacion_grasa = "Muy Alto/Obesidad"
                    elif 60 <= edad <= 79:
                        if porcentaje_grasa < 24:
                            interpretacion_grasa = "Bajo/Magro"
                        elif 24 <= porcentaje_grasa <= 35.9:
                            interpretacion_grasa = "Normal/Saludable"
                        elif 36 <= porcentaje_grasa <= 41.9:
                            interpretacion_grasa = "Alto/Sobrepeso"
                        else:
                            interpretacion_grasa = "Muy Alto/Obesidad"
                
                # Si la edad está fuera de los rangos, usar interpretación general
                if not interpretacion_grasa:
                    if sexo == "M":
                        if porcentaje_grasa <= 15:
                            interpretacion_grasa = "Bajo (atlético)"
                        elif porcentaje_grasa <= 25:
                            interpretacion_grasa = "Normal"
                        else:
                            interpretacion_grasa = "Alto"
                    else:
                        if porcentaje_grasa <= 25:
                            interpretacion_grasa = "Bajo (atlético)"
                        elif porcentaje_grasa <= 35:
                            interpretacion_grasa = "Normal"
                        else:
                            interpretacion_grasa = "Alto"
                
                # 5. ÍNDICE DE MASA LIBRE DE GRASA (IMLG)
                # Paso 1: Convertir % de grasa a kg de grasa
                kg_grasa = round((porcentaje_grasa / 100) * peso, 2)
                
                # Paso 2: Calcular masa libre de grasa (peso total - kg de grasa)
                masa_libre_grasa = round(peso - kg_grasa, 2)
                
                # Paso 3: Calcular índice de masa libre de grasa (MLG / Talla²)
                imlg = round(masa_libre_grasa / (altura ** 2), 2)
                
                # Interpretación del IMLG según sexo
                interpretacion_imlg = ""
                if sexo == "M":  # Hombres
                    if imlg < 17:
                        interpretacion_imlg = "Desgastado/Bajo"
                    else:
                        interpretacion_imlg = "Normal"
                else:  # Mujeres
                    if imlg < 15:
                        interpretacion_imlg = "Desgastado/Bajo"
                    else:
                        interpretacion_imlg = "Normal"
                
                # 6. MASA GRASA (kg)
                # Fórmula: MG = (Peso × % de grasa) / 100
                masa_grasa_kg = round((peso * porcentaje_grasa) / 100, 2)
                
                # 7. MASA MAGRA (kg)
                # Fórmula: MM = Peso - Masa Grasa
                masa_magra_kg = round(peso - masa_grasa_kg, 2)
                
                # 8. AGUA CORPORAL TOTAL (ACT)
                # Fórmulas específicas por sexo
                if sexo == "M":  # Hombres
                    act = round(((peso * 69.81) - (0.26 * peso) - (0.12 * edad)) / 100, 2)
                else:  # Mujeres
                    act = round(((peso * 79.45) - (0.24 * peso) - (0.15 * edad)) / 100, 2)
                
                # 9. AGUA CORPORAL INTRACELULAR (ACI)
                # Fórmulas específicas por sexo usando ACT
                if sexo == "M":  # Hombres
                    porcentaje_aci = (52.3 - (0.07 * edad)) / 100
                    aci = round(porcentaje_aci * act, 2)
                else:  # Mujeres
                    porcentaje_aci = (62.3 - (0.16 * edad)) / 100
                    aci = round(porcentaje_aci * act, 2)
                
                # 10. AGUA CORPORAL EXTRACELULAR (AE)
                # Fórmula: AE = ACT - ACI
                ae = round(act - aci, 2)
                
                # 11. ÁREA DEL BRAZO (AB)
                # Fórmula: AB = (CMB)² / 12.5664
                area_brazo = round((cmb ** 2) / 12.5664, 2)
                
                # 12. ÁREA MUSCULAR DEL BRAZO (AMB)
                # Fórmula: AMB = ((CMB) - (3.1416 × PCT en cm))² / 12.5664
                # Nota: PCT ya está convertido a cm en pct_cm
                area_muscular_brazo = round(((cmb - (3.1416 * pct_cm)) ** 2) / 12.5664, 2)
                
                # 13. ÁREA GRASA DEL BRAZO (AGB)
                # Fórmula: AGB = AB - AMB
                area_grasa_brazo = round(area_brazo - area_muscular_brazo, 2)
                
                # 14. ÍNDICE DE ÁREA GRASA (IAG)
                # Fórmula: IAG = (AGB / AB) × 100
                iag = round((area_grasa_brazo / area_brazo) * 100, 2)
                
                # Interpretación del IAG según percentiles
                if iag < 5:
                    interpretacion_iag = "Desgastado"
                elif 5 <= iag < 15:
                    interpretacion_iag = "Debajo del promedio"
                elif 15 <= iag <= 85:
                    interpretacion_iag = "Promedio"
                elif 85 < iag <= 95:
                    interpretacion_iag = "Arriba del promedio"
                else:  # >95
                    interpretacion_iag = "Exceso de grasa"
                
                # 15. % PCT (Porcentaje del Pliegue Cutáneo Tricipital)
                # Valores de referencia según sexo
                if sexo == "M":  # Hombres
                    pct_referencia = 12.5  # mm
                else:  # Mujeres
                    pct_referencia = 16.5  # mm
                
                # Fórmula: % PCT = (PCT actual / PCT referencia) × 100
                porcentaje_pct = round((pct_mm / pct_referencia) * 100, 1)
                
                # Interpretación del % PCT según tabla
                if porcentaje_pct >= 100:
                    interpretacion_pct = "Normal"
                elif porcentaje_pct >= 65:
                    interpretacion_pct = "Desnutrición leve"
                elif porcentaje_pct >= 40:
                    interpretacion_pct = "Desnutrición moderada"
                else:  # <40%
                    interpretacion_pct = "Desnutrición severa"
                
                # 16. % CMB (Porcentaje de la Circunferencia Media del Brazo)
                # Valores de referencia según sexo
                if sexo == "M":  # Hombres
                    cmb_referencia = 25.3  # cm
                else:  # Mujeres
                    cmb_referencia = 23.2  # cm
                
                # Fórmula: % CMB = (CMB actual / CMB referencia) × 100
                porcentaje_cmb = round((cmb / cmb_referencia) * 100, 1)
                
                # Interpretación del % CMB según tabla
                if porcentaje_cmb >= 90:
                    interpretacion_cmb = "Normal"
                elif porcentaje_cmb >= 85:
                    interpretacion_cmb = "Desnutrición leve"
                elif porcentaje_cmb >= 75:
                    interpretacion_cmb = "Desnutrición moderada"
                else:  # <75%
                    interpretacion_cmb = "Desnutrición severa"
                
                # Cálculo básico del IMC para contexto
                imc = round(peso / (altura ** 2), 2)
                interpretacion_imc = ""
                for rango in formulas["imc"].get("interpretacion", []):
                    if imc >= rango["min"] and imc <= rango["max"]:
                        interpretacion_imc = rango["texto"]
                        break
                
                output_block = (
                    f"> Análisis de Composición Corporal\n\n"
                    f"DATOS DE ENTRADA:\n"
                    f"• Peso: {peso} kg\n"
                    f"• Altura: {altura} m ({altura_cm} cm)\n"
                    f"• Edad: {edad} años\n"
                    f"• Sexo: {sexo}\n"
                    f"• CMB: {cmb} cm\n"
                    f"• PCT: {pct_mm} mm ({pct_cm} cm)\n"
                    f"• PCB: {pcb_mm} mm\n"
                    f"• PCSE: {pcse_mm} mm\n"
                    f"• PCI: {pci_mm} mm\n"
                    f"• Suma de pliegues: {suma_pliegues} mm\n\n"
                    f"CÁLCULO 1 - ÁREA MUSCULAR BRAQUIAL DISPONIBLE:\n"
                    f"AMBd = [CMB - (π × PCT)]² / (4π) + constante\n"
                    f"AMBd = [{cmb} - (π × {pct_cm})]² / (4π) + {constante}\n"
                    f"AMBd = {ambd} cm²\n\n"
                    f"CÁLCULO 2 - MASA MUSCULAR TOTAL:\n"
                    f"MMT = Talla (cm) × [(0.0264) + (0.0029 × AMBd)]\n"
                    f"MMT = {altura_cm} × [(0.0264) + (0.0029 × {ambd})]\n"
                    f"MMT = {altura_cm} × [{factor_1} + {factor_2:.4f}]\n"
                    f"MMT = {altura_cm} × {factor_1 + factor_2:.4f}\n"
                    f"MMT = {mmt} kg\n\n"
                    f"CÁLCULO 3 - DENSIDAD CORPORAL:\n"
                    f"D = c - [m × log₁₀(suma de pliegues)]\n"
                    f"D = {c} - [{m} × log₁₀({suma_pliegues})]\n"
                    f"D = {c} - [{m} × {math.log10(suma_pliegues):.4f}]\n"
                    f"D = {densidad} g/cm³\n\n"
                    f"CÁLCULO 4 - PORCENTAJE DE GRASA:\n"
                    f"% Grasa = (4.95/Densidad - 4.5) × 100\n"
                    f"% Grasa = (4.95/{densidad} - 4.5) × 100\n"
                    f"% Grasa = ({4.95/densidad:.4f} - 4.5) × 100\n"
                    f"% Grasa = {porcentaje_grasa}%\n\n"
                    f"INTERPRETACIÓN DE % GRASA (NIH/OMS):\n"
                    f"Sexo: {sexo} | Edad: {edad} años\n"
                    f"Porcentaje de grasa: {porcentaje_grasa}% → {interpretacion_grasa}\n\n"
                    f"CÁLCULO 5 - ÍNDICE DE MASA LIBRE DE GRASA:\n"
                    f"Paso 1: Kg de grasa = ({porcentaje_grasa}% / 100) × {peso} kg = {kg_grasa} kg\n"
                    f"Paso 2: Masa libre de grasa = {peso} kg - {kg_grasa} kg = {masa_libre_grasa} kg\n"
                    f"Paso 3: IMLG = MLG / Talla² = {masa_libre_grasa} / ({altura})² = {imlg} kg/m²\n\n"
                    f"CÁLCULO 6 - MASA GRASA (kg):\n"
                    f"MG = (Peso × % de grasa) / 100\n"
                    f"MG = ({peso} × {porcentaje_grasa}) / 100\n"
                    f"MG = {masa_grasa_kg} kg\n\n"
                    f"CÁLCULO 7 - MASA MAGRA (kg):\n"
                    f"MM = Peso - Masa Grasa\n"
                    f"MM = {peso} - {masa_grasa_kg}\n"
                    f"MM = {masa_magra_kg} kg\n\n"
                    f"CÁLCULO 8 - AGUA CORPORAL TOTAL (ACT):\n"
                    f"Fórmula ({sexo}): ACT = (peso × {'69.81' if sexo == 'M' else '79.45'}) - ({'0.26' if sexo == 'M' else '0.24'} × peso) - ({'0.12' if sexo == 'M' else '0.15'} × edad) / 100\n"
                    f"ACT = ({peso} × {'69.81' if sexo == 'M' else '79.45'}) - ({'0.26' if sexo == 'M' else '0.24'} × {peso}) - ({'0.12' if sexo == 'M' else '0.15'} × {edad}) / 100\n"
                    f"ACT = {act} litros\n\n"
                    f"CÁLCULO 9 - AGUA CORPORAL INTRACELULAR (ACI):\n"
                    f"Fórmula ({sexo}): ACI = [({'52.3' if sexo == 'M' else '62.3'} - ({'0.07' if sexo == 'M' else '0.16'} × edad)) / 100] × ACT\n"
                    f"ACI = [({'52.3' if sexo == 'M' else '62.3'} - ({'0.07' if sexo == 'M' else '0.16'} × {edad})) / 100] × {act}\n"
                    f"ACI = [{porcentaje_aci:.3f}] × {act} = {aci} litros\n\n"
                    f"CÁLCULO 10 - AGUA CORPORAL EXTRACELULAR (AE):\n"
                    f"AE = ACT - ACI\n"
                    f"AE = {act} - {aci}\n"
                    f"AE = {ae} litros\n\n"
                    f"CÁLCULO 11 - ÁREA DEL BRAZO (AB):\n"
                    f"AB = (CMB)² / 12.5664\n"
                    f"AB = ({cmb})² / 12.5664\n"
                    f"AB = {area_brazo} cm²\n\n"
                    f"CÁLCULO 12 - ÁREA MUSCULAR DEL BRAZO (AMB):\n"
                    f"AMB = ((CMB) - (3.1416 × PCT en cm))² / 12.5664\n"
                    f"AMB = (({cmb}) - (3.1416 × {pct_cm}))² / 12.5664\n"
                    f"AMB = ({cmb - (3.1416 * pct_cm):.4f})² / 12.5664\n"
                    f"AMB = {area_muscular_brazo} cm²\n\n"
                    f"CÁLCULO 13 - ÁREA GRASA DEL BRAZO (AGB):\n"
                    f"AGB = AB - AMB\n"
                    f"AGB = {area_brazo} - {area_muscular_brazo}\n"
                    f"AGB = {area_grasa_brazo} cm²\n\n"
                    f"CÁLCULO 14 - ÍNDICE DE ÁREA GRASA (IAG):\n"
                    f"IAG = (AGB / AB) × 100\n"
                    f"IAG = ({area_grasa_brazo} / {area_brazo}) × 100\n"
                    f"IAG = {iag}%\n\n"
                    f"CÁLCULO 15 - % PCT (PORCENTAJE PLIEGUE CUTÁNEO TRICIPITAL):\n"
                    f"Valor de referencia ({sexo}): {pct_referencia} mm\n"
                    f"% PCT = (PCT actual / PCT referencia) × 100\n"
                    f"% PCT = ({pct_mm} / {pct_referencia}) × 100\n"
                    f"% PCT = {porcentaje_pct}%\n\n"
                    f"CÁLCULO 16 - % CMB (PORCENTAJE CIRCUNFERENCIA MEDIA DEL BRAZO):\n"
                    f"Valor de referencia ({sexo}): {cmb_referencia} cm\n"
                    f"% CMB = (CMB actual / CMB referencia) × 100\n"
                    f"% CMB = ({cmb} / {cmb_referencia}) × 100\n"
                    f"% CMB = {porcentaje_cmb}%\n\n"
                    f"RESULTADOS:\n"
                    f"┌─ IMC: {imc} kg/m² ({interpretacion_imc})\n"
                    f"├─ Área Muscular Braquial: {ambd} cm²\n"
                    f"├─ Porcentaje AMBd: {porcentaje_ambd}%\n"
                    f"├─ Estado muscular: {interpretacion_ambd}\n"
                    f"├─ Masa Muscular Total: {mmt} kg\n"
                    f"├─ Densidad Corporal: {densidad} g/cm³\n"
                    f"├─ Porcentaje de Grasa: {porcentaje_grasa}% ({interpretacion_grasa})\n"
                    f"├─ Masa Grasa: {masa_grasa_kg} kg\n"
                    f"├─ Masa Magra: {masa_magra_kg} kg\n"
                    f"├─ Masa Libre de Grasa: {masa_libre_grasa} kg\n"
                    f"├─ Índice MLG: {imlg} kg/m² ({interpretacion_imlg})\n"
                    f"├─ Agua Corporal Total: {act} L\n"
                    f"├─ Agua Intracelular: {aci} L\n"
                    f"├─ Agua Extracelular: {ae} L\n"
                    f"├─ Área del Brazo: {area_brazo} cm²\n"
                    f"├─ Área Muscular del Brazo: {area_muscular_brazo} cm²\n"
                    f"├─ Área Grasa del Brazo: {area_grasa_brazo} cm²\n"
                    f"├─ Índice de Área Grasa: {iag}% ({interpretacion_iag})\n"
                    f"├─ % PCT: {porcentaje_pct}% ({interpretacion_pct})\n"
                    f"└─ % CMB: {porcentaje_cmb}% ({interpretacion_cmb})\n\n"
                    f"INTERPRETACIÓN CLÍNICA:\n"
                    f"• Estado nutricional: {interpretacion_imc}\n"
                    f"• Estado muscular del brazo: {interpretacion_ambd}\n"
                    f"• Área muscular disponible: {ambd} cm² ({porcentaje_ambd}% de referencia)\n"
                    f"• Masa muscular corporal total: {mmt} kg ({interpretacion_mmt})\n"
                    f"• Densidad corporal: {densidad} g/cm³ ({interpretacion_densidad})\n"
                    f"• Grasa corporal según NIH/OMS: {porcentaje_grasa}% ({interpretacion_grasa})\n"
                    f"• Masa grasa corporal: {masa_grasa_kg} kg\n"
                    f"• Masa magra corporal: {masa_magra_kg} kg\n"
                    f"• Índice de masa libre de grasa: {imlg} kg/m² ({interpretacion_imlg})\n"
                    f"• Agua corporal total: {act} L ({round((act/peso)*100, 1)}% del peso corporal)\n"
                    f"• Agua intracelular: {aci} L ({round((aci/act)*100, 1)}% del ACT)\n"
                    f"• Agua extracelular: {ae} L ({round((ae/act)*100, 1)}% del ACT)\n"
                    f"• Análisis del brazo: Área total {area_brazo} cm², músculo {area_muscular_brazo} cm², grasa {area_grasa_brazo} cm²\n"
                    f"• Índice de área grasa del brazo: {iag}% ({interpretacion_iag})\n"
                    f"• Evaluación nutricional por PCT: {porcentaje_pct}% del valor de referencia ({interpretacion_pct})\n"
                    f"• Evaluación nutricional por CMB: {porcentaje_cmb}% del valor de referencia ({interpretacion_cmb})"
                )
                
                print(f"[DEBUG COMPOSICIÓN] ¡CÁLCULO COMPLETADO EXITOSAMENTE!")
                print(f"[DEBUG COMPOSICIÓN] Longitud del output: {len(output_block)} caracteres")
                
                return {
                    "message": "",
                    "console_block": {
                        "title": "Composición Corporal",
                        "input": "",
                        "output": output_block
                    }
                }
            except Exception as e:
                print(f"[DEBUG COMPOSICIÓN] ¡ERROR EN CÁLCULO!: {str(e)}")
                print(f"[DEBUG COMPOSICIÓN] Tipo de error: {type(e)}")
                import traceback
                print(f"[DEBUG COMPOSICIÓN] Stack trace: {traceback.format_exc()}")
                return {
                    "message": f"Error al calcular la composición corporal: {str(e)}",
                    "console_block": {
                        "title": "Composición Corporal",
                        "input": "-",
                        "output": f"RESULTADO:\nError al calcular: {str(e)}"
                    }
                }
    
    # Detectar si se está pidiendo un cálculo que no conocemos
    terminos_calculo = [
        "calcular", "calculo", "cálculo", "formula", "fórmula", 
        "densidad corporal", "masa grasa", "masa magra", "porcentaje grasa",
        "tasa metabolica", "gasto energetico", "requerimiento", "tmb", "get"
    ]
    es_solicitud_calculo = any(termino in prompt.lower() for termino in terminos_calculo)
    
    if es_solicitud_calculo and not formula_key:
        return {
            "message": "Lo siento, no tengo información específica sobre ese cálculo en mi base de datos de fórmulas. Puedo ayudarte con: IMC, composición corporal completa, TMB (Harris-Benedict), agua corporal, y requerimiento de proteína. ¿Te interesa alguno de estos?",
            "console_block": None
        }
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
        
        # Evitar que repita instrucciones del sistema
        instrucciones_sistema = [
            "responde exclusivamente sobre el alimento proporcionado",
            "no mezcles ni inventes otros",
            "evita responder con historias personales", 
            "responde siempre en español",
            "de forma breve, clara y profesional",
            "si no sabes algo con certeza",
            "admite tu límite con honestidad",
            "nunca repitas literalmente el mensaje del usuario",
            "calyx ai",
            "asistente inteligente",
            "especializado en nutrición"
        ]
        
        respuesta_lower = respuesta.lower()
        if any(instr in respuesta_lower for instr in instrucciones_sistema):
            return "Lo siento, no tengo información específica sobre eso en este momento. ¿Hay algo más en lo que pueda ayudarte?"
        
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

    # Instrucción de sistema optimizada para Phi-3 como asistente nutricional
    system_instruction = (
        "<|system|>\n"
        "Eres Calyx AI, un asistente nutricional profesional especializado. Tu función principal es:\n\n"
        
        "**PRIORIDADES:**\n"
        "1. NUTRICIÓN: Proporcionar información nutricional precisa de alimentos usando tu base de datos\n"
        "2. CÁLCULOS: Realizar cálculos médicos (IMC, composición corporal) cuando se soliciten\n"
        "3. CONSULTAS GENERALES: Responder preguntas apropiadas de salud y bienestar\n\n"
        
        "**CAPACIDADES ESPECÍFICAS:**\n"
        "- Acceso a base de datos SMAE con información nutricional de alimentos argentinos\n"
        "- Cálculos médicos: IMC, composición corporal, pliegues cutáneos, densidad corporal\n"
        "- Interpretación de resultados según estándares OMS/NIH\n"
        "- Análisis nutricional por porciones específicas\n\n"
        
        "**ESTILO DE RESPUESTA:**\n"
        "- CONCISO: Respuestas directas, máximo 2-3 oraciones\n"
        "- PROFESIONAL: Lenguaje técnico apropiado pero comprensible\n"
        "- BASADO EN DATOS: Solo información verificable de tu base de datos\n"
        "- SIN RELLENO: No agregues frases introductorias innecesarias\n\n"
        
        "**RESTRICCIONES:**\n"
        "- NO inventes datos nutricionales\n"
        "- NO proporciones consejos médicos específicos\n"
        "- NO repitas textualmente las preguntas del usuario\n"
        "- NO uses experiencias personales o anécdotas\n\n"
        
        "**FORMATO ESPERADO:**\n"
        "Para alimentos: Información nutricional directa (kcal, proteínas, grasas, carbohidratos)\n"
        "Para cálculos: Usa el sistema console_block cuando corresponda\n"
        "Para saludos: Respuesta amigable pero breve\n\n"
        
        f"{contexto_nutricional}\n"
        
        "Responde siempre en español y mantén el foco en nutrición y salud.\n"
    )
    # Si se trata de cálculo de IMC y ya se devolvió el resultado, no continuar con el prompt normal
    if formula_key and formula_key.lower() == "imc" and not faltantes:
        # Ya se devolvió el resultado arriba
        return  # return explícito para evitar continuar
    # Prompt reforzado para respuestas cerradas y profesionales
    prompt_final = f"{system_instruction}<|user|>\n{prompt}\n<|assistant|>\n"
    
    # *** FALLBACK RÁPIDO PARA SALUDOS SIMPLES ***
    # Si es un saludo simple y no hay fórmula, usar respuesta rápida
    if not formula_key:
        lineas = prompt.strip().split('\n')
        ultimo_mensaje = ""
        for linea in reversed(lineas):
            if linea.strip() and not linea.strip().startswith('ai:'):
                ultimo_mensaje = linea.strip().lower()
                if ultimo_mensaje.startswith('user:'):
                    ultimo_mensaje = ultimo_mensaje[5:].strip()
                break
        
        # Saludos simples - respuesta inmediata sin AI
        saludos_simples = ["hola", "hello", "hi", "buenas", "buenos días", "buenas tardes", "buenas noches"]
        if ultimo_mensaje and any(saludo == ultimo_mensaje.strip() for saludo in saludos_simples):
            print(f"[DEBUG] Fallback rápido para saludo: '{ultimo_mensaje}'")
            return {"message": "¡Hola! Soy CalyxAI, tu asistente nutricional. ¿En qué puedo ayudarte hoy? Puedo buscar información nutricional de alimentos o calcular tu IMC."}
    
    if not get_ia_engine().is_ready():
        status = get_ia_engine().get_status()
        print(f"[LOG] /chat error: IA engine not ready: {status['message']}")
        return JSONResponse({"error": status["message"]}, status_code=503 if status["status"]=="loading" else 500)
    try:
        # --- Parámetros de generación optimizados para Phi-3 nutricional ---
        gen_args = {
            "max_new_tokens": 120,  # Respuestas más concisas y precisas
            "temperature": 0.3,     # Menos creatividad, más consistencia
            "top_p": 0.8,           # Enfoque en tokens más probables
            "top_k": 30,            # Limitar vocabulario para mayor precisión
            "repetition_penalty": 1.1,  # Evitar repeticiones
            "do_sample": True
        }
        stop_tokens = ["<|user|>", "<|system|>", "<|assistant|>", "\n\n", "Usuario:", "Pregunta:"]
        import inspect
        sig = inspect.signature(get_ia_engine().generate)
        if any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values()):
            response = get_ia_engine().generate(prompt_final, stop=stop_tokens, **gen_args)
        else:
            response = get_ia_engine().generate(prompt_final)
        for stop in stop_tokens:
            idx = response.find(stop)
            if idx != -1:
                response = response[:idx]
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
        clean_response = None
        for l in lines:
            l_strip = l.strip()
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
                if es_nutricion and re.search(r"(es una|es un|es la|es el|sirve|utilizada|utilizado|perfecta|perfecto|acompañamiento|versátil|fresca|fresco|base sana|preparaciones|ensalada|plato principal|platos más elaborados|picada|picado|junto|otros vegetales|cruda|crudo|hamburguesas|preparaciones saladas|ingredientes para ensalada|ingrediente para ensalada|ingredientes para ensaladas|ingrediente para ensaladas)", l_strip, re.IGNORECASE):
                    continue
                clean_response = l_strip
                break
        if not clean_response:
            clean_response = next((l.strip() for l in lines if l.strip() and l.strip().lower() != prompt.strip().lower()), response.strip())
        clean_response = postprocesar_respuesta(prompt, clean_response)
        print(f"[LOG] /chat response: {clean_response}")
        # SIEMPRE devolver message y console_block (null)
        return {"message": clean_response, "console_block": None}
    except Exception as e:
        print(f"[LOG] /chat exception: {e}")
        return JSONResponse({"error": f"Ocurrió un error al generar la respuesta: {str(e)}"}, status_code=500)


@app.get("/")
def root():
    return {"message": "Calyx AI backend activo (Phi-3 Mini-4K-Instruct)"}

@app.get("/model/status")
def get_model_status():
    """Endpoint para verificar el estado del modelo Phi-3"""
    try:
        import os
        from pathlib import Path
        
        # Verificar estado del motor de IA - USAR INSTANCIA GLOBAL
        if not hasattr(app.state, 'ai_engine') or app.state.ai_engine is None:
            # Usar la instancia global existente en lugar de crear nueva
            print("[DEBUG] Usando instancia global de IAEngine existente")
            app.state.ai_engine = get_ia_engine()
        
        ai_engine = app.state.ai_engine
        
        # Verificar si el modelo está listo
        if ai_engine.is_ready():
            return {
                "status": "ready",
                "message": "Modelo Phi-3 cargado y listo para usar",
                "model_ready": True,
                "model_name": ai_engine.model_name,
                "device": ai_engine.device
            }
        elif ai_engine.model_error:
            return {
                "status": "error", 
                "message": f"Error en el modelo: {ai_engine.model_error}",
                "model_ready": False,
                "model_name": ai_engine.model_name
            }
        else:
            return {
                "status": "loading",
                "message": "Modelo en proceso de carga...",
                "model_ready": False,
                "model_name": ai_engine.model_name
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al verificar el estado del modelo: {str(e)}",
            "model_ready": False,
            "model_name": "microsoft/phi-3-mini-4k-instruct"
        }

@app.post("/model/download")
async def download_model():
    """Endpoint para simular la descarga del modelo"""
    try:
        # En una implementación real, aquí iniciaríamos la descarga del modelo
        # Por ahora, simulamos que se está descargando
        return {
            "status": "download_started",
            "message": "Descarga del modelo iniciada",
            "estimated_size_mb": 2400,
            "estimated_time_minutes": 5
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al iniciar la descarga: {str(e)}"
        }

@app.get("/model/download/progress")
async def get_download_progress():
    """Endpoint para obtener el progreso de descarga del modelo"""
    # En una implementación real, esto devolvería el progreso real
    # Por ahora, simulamos un progreso
    import random
    progress = random.randint(0, 100)
    
    return {
        "status": "downloading" if progress < 100 else "completed",
        "progress_percentage": progress,
        "downloaded_mb": (2400 * progress) // 100,
        "total_mb": 2400,
        "speed_mbps": random.uniform(5.0, 15.0),
        "time_remaining_minutes": max(0, (100 - progress) // 10)
    }
