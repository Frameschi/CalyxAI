from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sqlite3
import json
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
    Maneja diferentes formatos de thinking que puede usar DeepSeek-R1.
    También maneja respuestas que empiezan con "json { " como JSON directo.
    """
    import re
    import json
    
    # Primero verificar si la respuesta es JSON directo (empieza con "json { ")
    json_pattern = r'^\s*json\s*\{'
    if re.match(json_pattern, response.strip(), re.IGNORECASE):
        try:
            # Extraer el JSON de la respuesta
            json_match = re.search(r'json\s*(\{.*\})', response, re.DOTALL | re.IGNORECASE)
            if json_match:
                json_data = json.loads(json_match.group(1))
                # Si es JSON válido, devolver como respuesta final sin thinking
                return None, json.dumps(json_data, ensure_ascii=False)
        except json.JSONDecodeError:
            pass  # Continuar con el parsing normal
    
    # Patrones posibles de thinking
    patterns = [
        r'<think>(.*?)</think>',  # <think>contenido</think>
        r'<thinking>(.*?)</thinking>',  # <thinking>contenido</thinking>
        r'```thinking\s*(.*?)\s*```',  # ```thinking contenido ```
        r'^\s*Thinking:(.*?)(?=\n\n|\n[A-Z]|$)',  # Thinking: contenido
        r'^\s*Razonamiento:(.*?)(?=\n\n|\n[A-Z]|$)',  # Razonamiento: contenido
    ]
    
    for pattern in patterns:
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE | re.MULTILINE)
        if match:
            thinking_content = match.group(1).strip()
            # Remover el bloque de thinking del mensaje final
            final_message = re.sub(pattern, '', response, flags=re.DOTALL | re.IGNORECASE).strip()
            # Limpiar líneas vacías extras
            final_message = re.sub(r'\n\s*\n\s*\n+', '\n\n', final_message)
            return thinking_content, final_message
    
    # Si no encuentra patrón específico, buscar líneas que parezcan thinking
    lines = response.split('\n')
    thinking_lines = []
    content_lines = []
    in_thinking = False
    
    for line in lines:
        line_lower = line.lower().strip()
        if line_lower.startswith(('think:', 'thinking:', 'razonamiento:', 'razonando:')) or '<think' in line_lower:
            in_thinking = True
            thinking_lines.append(line)
        elif in_thinking and (line.strip() == '' or len(line.strip()) < 10):
            # Línea vacía o muy corta, podría ser fin del thinking
            continue
        elif in_thinking and line_lower.startswith(('respuesta:', 'conclusión:', 'finalmente:')):
            # Fin del thinking
            in_thinking = False
            content_lines.append(line)
        elif in_thinking:
            thinking_lines.append(line)
        else:
            content_lines.append(line)
    
    if thinking_lines:
        thinking_content = '\n'.join(thinking_lines).strip()
        final_message = '\n'.join(content_lines).strip()
        return thinking_content, final_message
    
    # No hay thinking detectable, devolver respuesta completa
    return None, response

def get_tokens_for_formula(formula_key):
    """Determina el número óptimo de tokens basado en la complejidad de la fórmula"""
    # Cálculos ultra-extensos que requieren muchos tokens
    ultra_complex = ['composicion_corporal']
    if formula_key in ultra_complex:
        return 1500  # Suficiente para desglose completo de múltiples fórmulas
    
    # Cálculos complejos con varios parámetros
    complex_formulas = ['tmb_harris_benedict', 'geb_schofield', 'calculo_calorico']
    if formula_key in complex_formulas:
        return 1000
    
    # Cálculos simples - aumentar para asegurar completitud
    return 800  # Suficiente para IMC y cálculos básicos con formato completo

def calculate_formula_from_json(formula_name, message):
    """
    Calcula una fórmula médica consultando data_formulas.json y extrayendo parámetros del mensaje.
    """
    import json
    import re
    import os
    
    try:
        # Cargar data_formulas.json
        formulas_path = os.path.join(os.path.dirname(__file__), "data_formulas.json")
        with open(formulas_path, 'r', encoding='utf-8') as f:
            formulas_data = json.load(f)
        
        # Verificar si la fórmula existe
        if formula_name not in formulas_data:
            return None
            
        formula = formulas_data[formula_name]
        
        # Extraer parámetros del mensaje según la definición de la fórmula
        extracted_params = {}
        
        for param in formula["parametros"]:
            param_name = param["nombre"]
            param_type = param["tipo"]
            param_unit = param.get("unidad", "")
            
            # Crear patrón de búsqueda para este parámetro
            if param_unit in ["kg", "kilogramos"]:
                pattern = r'(\d+(?:\.\d+)?)\s*(?:kg|kilogramos?)'
            elif param_unit in ["m", "metros"]:
                pattern = r'(\d+(?:\.\d+)?)\s*(?:m|metros?)'
            elif param_unit in ["cm", "centímetros"]:
                pattern = r'(\d+(?:\.\d+)?)\s*(?:cm|centímetros?)'
            elif param_unit == "años":
                pattern = r'(\d+)\s*(?:años?|edad)'
            elif param_name == "sexo":
                pattern = r'(?:hombre|varón|masculino|m)\s*(?:\w*\s*)*|(?:mujer|femenino|f)\s*(?:\w*\s*)*'
            else:
                continue
                
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                if param_name == "sexo":
                    # Determinar sexo basado en palabras clave
                    text_found = match.group(0).lower()
                    if any(word in text_found for word in ['hombre', 'varón', 'masculino', 'm']):
                        value = "M"
                    elif any(word in text_found for word in ['mujer', 'femenino', 'f']):
                        value = "F"
                    else:
                        value = "M"  # default
                else:
                    value = float(match.group(1)) if param_type == "float" else int(match.group(1))
                extracted_params[param_name] = value
        
        # Verificar que tenemos todos los parámetros necesarios
        required_params = [p["nombre"] for p in formula["parametros"]]
        if not all(param in extracted_params for param in required_params):
            return None
            
        # Calcular IMC
        if formula_name == "imc":
            peso = extracted_params["peso"]
            altura = extracted_params["altura"]
            
            # Cálculos paso a paso
            altura_cuadrado = round(altura ** 2, 4)
            imc_value = round(peso / altura_cuadrado, 2)
            
            # Determinar interpretación
            interpretation = "Sin clasificar"
            for rango in formula["interpretacion"]:
                if rango["min"] <= imc_value < rango["max"]:
                    interpretation = rango["texto"]
                    break
            
            # Devolver datos estructurados para que DeepSeek-R1 los formatee creativamente
            return {
                "tipo": "calculo_medico",
                "formula": formula_name.upper(),
                "nombre_completo": formula["nombre"],
                "parametros": extracted_params,
                "calculos": {
                    "pasos": [
                        f"Elevar altura al cuadrado: {altura}² = {altura_cuadrado}",
                        f"Dividir peso entre altura²: {peso} ÷ {altura_cuadrado} = {imc_value}"
                    ],
                    "resultado": imc_value,
                    "unidad": "kg/m²",
                    "formula_matematica": "IMC = peso / altura²"
                },
                "interpretacion": interpretation,
                "categoria": formula.get("categoria", ""),
                "descripcion": formula.get("descripcion", "")
            }
            
        # Calcular TMB Harris-Benedict
        elif formula_name == "tmb_harris_benedict":
            peso = extracted_params["peso"]
            altura = extracted_params["altura"]  # en cm
            edad = extracted_params["edad"]
            sexo = extracted_params.get("sexo", "M").upper()
            
            # Fórmula Harris-Benedict
            if sexo == "M":  # Hombre
                constante = 66.5
                factor_peso = 13.75
                factor_altura = 5.003
                factor_edad = 6.775
                tmb = constante + (factor_peso * peso) + (factor_altura * altura) - (factor_edad * edad)
            else:  # Mujer
                constante = 655.1
                factor_peso = 9.563
                factor_altura = 1.850
                factor_edad = 4.676
                tmb = constante + (factor_peso * peso) + (factor_altura * altura) - (factor_edad * edad)
            
            tmb_value = round(tmb, 1)
            
            # Determinar interpretación
            interpretation = "Sin clasificar"
            for rango in formula["interpretacion"]:
                if rango["min"] <= tmb_value < rango["max"]:
                    interpretation = rango["texto"]
                    break
            
            # Devolver datos estructurados
            return {
                "tipo": "calculo_medico",
                "formula": formula_name.upper(),
                "nombre_completo": formula["nombre"],
                "parametros": extracted_params,
                "calculos": {
                    "pasos": [
                        f"Constante base: {constante}",
                        f"Factor peso: {factor_peso} × {peso} = {round(factor_peso * peso, 1)}",
                        f"Factor altura: {factor_altura} × {altura} = {round(factor_altura * altura, 1)}",
                        f"Factor edad: {factor_edad} × {edad} = {round(factor_edad * edad, 1)}",
                        f"Cálculo final: {constante} + {round(factor_peso * peso, 1)} + {round(factor_altura * altura, 1)} - {round(factor_edad * edad, 1)} = {tmb_value}"
                    ],
                    "resultado": tmb_value,
                    "unidad": "kcal/día",
                    "formula_matematica": f"{'Hombre' if sexo == 'M' else 'Mujer'}: {constante} + ({factor_peso} × peso) + ({factor_altura} × altura) - ({factor_edad} × edad)"
                },
                "interpretacion": interpretation,
                "categoria": formula.get("categoria", ""),
                "descripcion": formula.get("descripcion", "")
            }
            
    except Exception as e:
        print(f"[ERROR] Error calculando fórmula {formula_name}: {e}")
        return None
    
    return None

def format_calculation_response(message):
    """
    Detecta si el mensaje es un cálculo y lo formatea para console_block.
    Ahora consulta data_formulas.json para cálculos reales.
    """
    import re
    
    # Detectar cálculos de IMC
    if re.search(r'IMC|índice.*masa.*corporal', message, re.IGNORECASE):
        result = calculate_formula_from_json("imc", message)
        if result:
            return result
    
    # Detectar otros tipos de cálculos (calorías, etc.) - lógica anterior
    if 'calorías' in message.lower() or 'kcal' in message.lower():
        # Formatear cálculo de calorías
        food_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:g|gramos?)\s+(?:de\s+)?([a-zA-Záéíóúñ\s]+)', message, re.IGNORECASE)
        kcal_match = re.search(r'(\d+(?:\.\d+)?)\s*kcal', message, re.IGNORECASE)
        
        if food_match and kcal_match:
            amount = food_match.group(1)
            food = food_match.group(2).strip()
            kcal = kcal_match.group(1)
            
            input_text = f"Alimento: {food}\nCantidad: {amount}g"
            output_text = f"Calorías: {kcal} kcal"
            
            return {
                "title": "Cálculo Calórico",
                "input": input_text,
                "output": output_text
            }
    
    return None

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

        # --- VERIFICAR SI EL USUARIO PIDE CÁLCULO DIRECTO DE FÓRMULA MÉDICA ---
        import re
        
        # Función para extraer solo el último mensaje del usuario del historial
        def extract_last_user_message(full_prompt):
            """Extrae solo el último mensaje del usuario del historial de conversación"""
            lines = full_prompt.strip().split('\n')
            user_messages = [line.replace('user:', '').strip() for line in lines if line.startswith('user:')]
            return user_messages[-1] if user_messages else full_prompt
        
        # Usar solo el último mensaje del usuario para detección de fórmulas
        last_user_message = extract_last_user_message(prompt)
        print(f"[LOG] Último mensaje del usuario: '{last_user_message}'")
        
        # Detectar pedidos de cálculos médicos - PATRONES EXPANDIDOS PARA TODAS LAS FÓRMULAS
        calculation_patterns = {
            "imc": r'calcula.*imc|imc.*calcula|cuál.*imc|mi.*imc|indice.*masa.*corporal',
            "tmb_harris_benedict": r'calcula.*tmb.*harris|tmb.*harris.*calcula|tasa.*metabolica.*basal.*harris|metabolismo.*basal.*harris',
            "tmb_mifflin": r'calcula.*tmb.*mifflin|tmb.*mifflin.*calcula|tasa.*metabolica.*mifflin|metabolismo.*basal.*mifflin',
            "tmb_owen": r'calcula.*tmb.*owen|tmb.*owen.*calcula|tasa.*metabolica.*owen|metabolismo.*basal.*owen',
            "tmb_fao_oms": r'calcula.*tmb.*fao|tmb.*fao.*calcula|tasa.*metabolica.*oms|metabolismo.*basal.*fao|metabolismo.*basal.*oms',
            "get": r'calcula.*get|get.*calcula|gasto.*energetico.*total|energia.*total',
            "icc": r'calcula.*icc|icc.*calcula|indice.*cintura.*cadera|cintura.*cadera',
            "ict": r'calcula.*ict|ict.*calcula|indice.*cintura.*altura|cintura.*altura',
            "peso_ideal": r'calcula.*peso.*ideal|peso.*ideal.*calcula|peso.*óptimo',
            "superficie_corporal": r'calcula.*superficie.*corporal|superficie.*corporal.*calcula|area.*corporal',
            "agua_corporal": r'calcula.*agua.*corporal|agua.*corporal.*calcula|hidratacion.*corporal',
            "requerimiento_proteina": r'calcula.*proteina|requerimiento.*proteina|proteina.*necesaria|necesidad.*proteina',
            "composicion_corporal": r'calcula.*composicion.*corporal|composicion.*corporal.*calcula|analisis.*corporal|composicion.*cuerpo',
        }
        
        for formula_name, pattern in calculation_patterns.items():
            if re.search(pattern, last_user_message, re.IGNORECASE):
                print(f"[LOG] Detectado pedido directo de {formula_name} en el último mensaje, calculando automáticamente...")
                calculation_data = calculate_formula_from_json(formula_name, prompt)
                if calculation_data:
                    # Enviar datos a DeepSeek-R1 para formateo creativo en console_block
                    # Usar get_ia_engine() para obtener la instancia
                    ia_engine = get_ia_engine()
                    if ia_engine is None:
                        return JSONResponse({"error": "AI engine not available"}, status_code=503)
                        
                    # Construir prompt optimizado usando el método centralizado en ai_engine
                    enhanced_prompt = ia_engine.build_calculation_prompt(prompt, calculation_data)
                    
                    # Determinar tokens basados en complejidad de la fórmula
                    max_tokens = get_tokens_for_formula(calculation_data['formula'])
                    response = ia_engine.generate(enhanced_prompt, max_new_tokens=max_tokens, temperature=0.1, top_p=0.3)
                    thinking_content, final_message = parse_deepseek_response(response)
                    
                    # DeepSeek-R1 debería responder con texto formateado, convertirlo en console_block
                    if final_message and len(final_message.strip()) > 10:  # Tiene contenido significativo
                        # Limpiar marcadores de código que pueda agregar DeepSeek-R1
                        import re
                        cleaned_message = re.sub(r'```\w*\n?', '', final_message)  # Remover ```plaintext, ```console, etc.
                        cleaned_message = re.sub(r'^\s*plaintext\s*', '', cleaned_message, flags=re.IGNORECASE)
                        cleaned_message = re.sub(r'^\s*console\s*', '', cleaned_message, flags=re.IGNORECASE)
                        cleaned_message = cleaned_message.strip()
                        
                        console_block = {
                            "title": f"Cálculo {calculation_data['formula']}",
                            "input": f"DATOS DE ENTRADA:\n" + "\n".join([f"{k.title()}: {v} {('kg' if k=='peso' else 'm' if k=='altura' else 'años' if k=='edad' else '')}" for k, v in calculation_data['parametros'].items()]),
                            "output": cleaned_message
                        }
                        return {"message": "Cálculo completado", "thinking": thinking_content, "console_block": console_block}
                    else:
                        # Fallback: devolver respuesta normal
                        return {"message": final_message or "Cálculo completado", "thinking": thinking_content, "console_block": None}

        # --- CONVERSACIONES NORMALES: usar generate() con system prompt general ---
        ia_engine = get_ia_engine()
        if ia_engine is None:
            return JSONResponse({"error": "AI engine not available"}, status_code=503)

        # Extraer último mensaje y historial para separar system y user
        last_user_message = extract_last_user_message(prompt)
        
        def extract_history_without_last(full_prompt):
            """Extrae el historial sin el último mensaje del usuario"""
            lines = full_prompt.strip().split('\n')
            # Si la última línea es user:, quitarla
            if lines and lines[-1].startswith('user:'):
                return '\n'.join(lines[:-1])
            return full_prompt
        
        history_without_last = extract_history_without_last(prompt)
        system_prompt_extra = f"HISTORIAL DE CONVERSACIÓN PARA CONTEXTO:\n{history_without_last}\n\n" if history_without_last.strip() else ""

        # Para conversaciones normales, usar generate_with_tools() con system prompt separado
        response = ia_engine.generate_with_tools(last_user_message, system_prompt_extra=system_prompt_extra, max_new_tokens=150, temperature=0.3, top_p=0.8, max_iterations=1)
        
        # Parsear respuesta de DeepSeek-R1 para separar thinking del mensaje final
        thinking_content, final_message = parse_deepseek_response(response)
        
        # Respuesta normal de conversación
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