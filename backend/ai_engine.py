# Imports para Transformers + Accelerate
import os
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    pipeline
)
from accelerate import Accelerator
import json
import re

class IAEngine:
    def __init__(self, model_name=None):
        # Configuración de modelos disponibles - Solo QWEN2.5-3B por ahora
        self.available_models = {
            "llama3.2": {
                "name": "Qwen/Qwen2.5-3B-Instruct",
                "engine": "transformers",
                "description": "Qwen2.5-3B - Rápido y eficiente",
                "quantization": "4bit"  # 4-bit quantization para GTX 1050 Ti
            }
            # Espacio reservado para modelo grande en el futuro
        }
        
        # Modelo por defecto - Llama 3.2 (principal)
        self.current_model_key = "llama3.2"
        current_model_config = self.available_models[self.current_model_key]
        self.model_name = model_name or current_model_config["name"]
        self.current_engine = current_model_config["engine"]

        # Variables para Transformers
        self.model_error = None
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self.accelerator = Accelerator()

        self._load_model()

    def _load_model(self):
        """Cargar modelo IA via Transformers (Qwen2.5-3B)"""
        if self.current_engine == "transformers":
            self._load_transformers_model()
        else:
            self.model_error = f"Engine no soportado: {self.current_engine}. Solo se soporta Transformers."

    def _load_transformers_model(self):
        """Cargar modelo usando Transformers + Accelerate con optimización GPU"""
        current_model_desc = self.available_models[self.current_model_key]["description"]
        quantization = self.available_models[self.current_model_key].get("quantization", "4bit")

        print(f"[IAEngine] [LOADING] Configurando {current_model_desc} con optimización GPU: {self.model_name}")

        try:
            # Configuración de cuantización 4-bit para Qwen2.5-3B
            if quantization == "4bit":
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
                print("[IAEngine] [CONFIG] Cuantización 4-bit activada para GPU GTX 1050 Ti")
            else:
                bnb_config = None

            # Cargar tokenizer
            print(f"[IAEngine] [LOADING] Cargando tokenizer: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )

            # Cargar modelo con configuración optimizada
            print(f"[IAEngine] [LOADING] Cargando modelo con cuantización {quantization}")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True,
                torch_dtype=torch.float16
            )

            # Crear pipeline para inference
            print("[IAEngine] [LOADING] Creando pipeline de inference")
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device_map="auto",
                torch_dtype=torch.float16
            )

            print(f"[IAEngine] [SUCCESS] {current_model_desc} cargado exitosamente con Transformers")
            self.model_error = None

        except Exception as e:
            error_msg = f"Error cargando modelo {self.model_name}: {str(e)}"
            print(f"[IAEngine] [ERROR] {error_msg}")
            self.model_error = error_msg
            self.model = None
            self.tokenizer = None
            self.pipeline = None

    def is_ready(self):
        """Verificar si el modelo está listo"""
        return self.model is not None and self.tokenizer is not None and self.model_error is None

    def get_status(self):
        """Obtener estado del modelo Transformers"""
        status_info = {
            "model_name": self.model_name,
            "engine": self.current_engine,
            "device": "cuda" if torch.cuda.is_available() else "cpu"
        }

        if self.model_error:
            status_info.update({
                "status": "error",
                "message": f"Modelo no disponible: {self.model_error}",
                "ready": False
            })
        elif self.is_ready():
            status_info.update({
                "status": "ready",
                "message": "Modelo cargado y listo para usar",
                "ready": True
            })
        else:
            status_info.update({
                "status": "loading",
                "message": "Cargando modelo...",
                "ready": False
            })

        return status_info

    def generate(self, prompt, system_prompt=None, max_new_tokens=120, temperature=0.3, top_p=0.8):
        """
        Generación usando Transformers
        """
        if not self.is_ready():
            raise RuntimeError("Modelo no está disponible. Verifica que esté cargado correctamente.")

        if self.current_engine == "transformers":
            return self._generate_transformers(prompt, system_prompt, max_new_tokens, temperature, top_p)
        else:
            raise RuntimeError(f"Engine no soportado: {self.current_engine}. Solo se soporta Transformers.")

    def _generate_transformers(self, user_prompt, system_prompt=None, max_new_tokens=300, temperature=0.3, top_p=0.8):
        """Generación usando Transformers + Accelerate con optimización GPU"""
        try:
            current_model_desc = self.available_models[self.current_model_key]["description"]
            print(f"[IAEngine] [GENERATE] Generando con {current_model_desc}, prompt length: {len(user_prompt)}")

            # Construir el prompt usando el chat template del modelo
            if system_prompt:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            else:
                messages = [{"role": "user", "content": user_prompt}]

            # Usar el chat template del tokenizer
            full_prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            # Generar respuesta usando el pipeline
            with torch.no_grad():
                outputs = self.pipeline(
                    full_prompt,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    return_full_text=False  # No repetir el prompt de entrada
                )

            # Extraer la respuesta generada
            generated_text = outputs[0]['generated_text']
            print(f"[IAEngine] [SUCCESS] Respuesta generada, length: {len(generated_text)}")

            return generated_text.strip()

        except Exception as e:
            error_msg = f"Error en generación con Transformers: {str(e)}"
            print(f"[IAEngine] [ERROR] {error_msg}")
            return "Lo siento, el modelo de IA no está disponible en este momento."

    def switch_model(self, model_key):
        """Cambiar entre modelos disponibles"""
        if model_key not in self.available_models:
            raise ValueError(f"Modelo '{model_key}' no disponible. Opciones: {list(self.available_models.keys())}")
        
        if model_key == self.current_model_key:
            print(f"[IAEngine] Modelo '{model_key}' ya está cargado")
            return True
        
        print(f"[IAEngine] Cambiando de '{self.current_model_key}' a '{model_key}'...")
        
        # Limpiar modelo actual de memoria
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self.model_error = None
        
        self._load_model()
        return self.is_ready()
    
    def get_current_model(self):
        """Obtener información del modelo actual"""
        model_info = self.available_models[self.current_model_key].copy()
        model_info.update({
            "key": self.current_model_key,
            "engine": self.current_engine,
            "is_ready": self.is_ready(),
            "available_models": {k: v["description"] for k, v in self.available_models.items()}
        })
        return model_info

    # ===== SISTEMA DE TOOLS/FUNCTIONS PARA CONSULTAS A BASE DE DATOS =====

    def get_available_tools(self):
        """Obtener lista de tools disponibles para el modelo"""
        return {
            "consultar_alimento": {
                "description": "Consultar información nutricional completa de un alimento específico en la base de datos",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nombre": {
                            "type": "string",
                            "description": "Nombre del alimento a buscar (ej: 'manzana', 'arroz', 'pollo')"
                        }
                    },
                    "required": ["nombre"]
                }
            },
            "buscar_alimentos_filtrados": {
                "description": "Buscar alimentos aplicando filtros nutricionales avanzados",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "criterios": {
                            "type": "object",
                            "description": "Criterios de filtro nutricional",
                            "properties": {
                                "sodio_max": {
                                    "type": "number",
                                    "description": "Máximo de sodio en mg (ej: 100 para alimentos bajos en sodio)"
                                },
                                "fibra_min": {
                                    "type": "number",
                                    "description": "Mínimo de fibra en g (ej: 5 para alimentos ricos en fibra)"
                                },
                                "calorias_max": {
                                    "type": "number",
                                    "description": "Máximo de calorías (ej: 200 para alimentos light)"
                                },
                                "proteina_min": {
                                    "type": "number",
                                    "description": "Mínimo de proteína en g (ej: 10 para alimentos proteicos)"
                                },
                                "lipidos_max": {
                                    "type": "number",
                                    "description": "Máximo de lípidos/grasas en g (ej: 5 para alimentos bajos en grasa)"
                                },
                                "grupo": {
                                    "type": "string",
                                    "description": "Grupo de alimentos específico (ej: 'verduras', 'frutas', 'cereales')"
                                },
                                "nombre_like": {
                                    "type": "string",
                                    "description": "Búsqueda por nombre parcial (ej: 'arroz' para encontrar variedades de arroz)"
                                }
                            }
                        },
                        "limite": {
                            "type": "number",
                            "description": "Máximo número de resultados (por defecto 10)",
                            "default": 10
                        }
                    },
                    "required": ["criterios"]
                }
            },
            "calcular_composicion_total": {
                "description": "Calcular la composición nutricional total de una combinación de alimentos",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "alimentos": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Lista de nombres de alimentos (ej: ['manzana', 'arroz integral'])"
                        },
                        "porciones": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Factores de porción para cada alimento (ej: [1.0, 2.0] para 1x manzana y 2x porción de arroz). Si no se especifica, usa 1.0 para todos"
                        }
                    },
                    "required": ["alimentos"]
                }
            },
            "generar_recomendaciones_dieta": {
                "description": "Generar recomendaciones de dieta basadas en restricciones y objetivos",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "restricciones": {
                            "type": "object",
                            "description": "Restricciones dietéticas",
                            "properties": {
                                "vegetariano": {"type": "boolean", "description": "Dieta vegetariana"},
                                "vegano": {"type": "boolean", "description": "Dieta vegana"},
                                "bajo_sodio": {"type": "boolean", "description": "Bajo en sodio"},
                                "alto_fibra": {"type": "boolean", "description": "Rico en fibra"},
                                "diabetico": {"type": "boolean", "description": "Apto para diabéticos"}
                            }
                        },
                        "objetivo_calorico": {
                            "type": "number",
                            "description": "Calorías objetivo diario (por defecto 2000)",
                            "default": 2000
                        }
                    },
                    "required": ["restricciones"]
                }
            },
            "obtener_formula": {
                "description": "Obtener la fórmula específica para un cálculo médico/nutricional",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tipo": {
                            "type": "string",
                            "description": "Tipo de fórmula/calculo (ej: 'imc', 'gasto_energetico_basal', 'superficie_corporal')"
                        }
                    },
                    "required": ["tipo"]
                }
            },
            "listar_formulas_disponibles": {
                "description": "Listar todas las fórmulas médicas disponibles en el sistema",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }

    def execute_tool(self, tool_name, parameters):
        """Ejecutar una tool específica con sus parámetros"""
        try:
            if tool_name == "consultar_alimento":
                return self._tool_consultar_alimento(parameters.get("nombre", ""))
            elif tool_name == "buscar_alimentos_filtrados":
                return self._tool_buscar_alimentos_filtrados(parameters.get("criterios", {}), parameters.get("limite", 10))
            elif tool_name == "calcular_composicion_total":
                return self._tool_calcular_composicion_total(parameters.get("alimentos", []), parameters.get("porciones"))
            elif tool_name == "generar_recomendaciones_dieta":
                return self._tool_generar_recomendaciones_dieta(parameters.get("restricciones", {}), parameters.get("objetivo_calorico", 2000))
            elif tool_name == "obtener_formula":
                return self._tool_obtener_formula(parameters.get("tipo", ""))
            elif tool_name == "listar_formulas_disponibles":
                return self._tool_listar_formulas()
            else:
                return {"error": f"Tool '{tool_name}' no encontrada"}
        except Exception as e:
            return {"error": f"Error ejecutando tool '{tool_name}': {str(e)}"}

    def _tool_consultar_alimento(self, nombre_alimento):
        """Tool para consultar información de un alimento"""
        if not nombre_alimento:
            return {"error": "Nombre de alimento requerido"}

        try:
            # Importar función de consulta de alimentos
            from main import get_alimentos_by_name

            columns, rows = get_alimentos_by_name(nombre_alimento)

            if not columns or not rows:
                return {
                    "encontrado": False,
                    "mensaje": f"No se encontró información para '{nombre_alimento}' en la base de datos"
                }

            # Obtener el alimento más relevante
            alimento_dict = dict(zip(columns, rows[0]))

            return {
                "encontrado": True,
                "alimento": alimento_dict.get('alimento', 'N/A'),
                "grupo": alimento_dict.get('grupo de alimentos', 'N/A'),
                "cantidad_base": f"{alimento_dict.get('cantidad', '100')} {alimento_dict.get('unidad', 'g')}",
                "valores_nutricionales": {
                    "energia_kcal": alimento_dict.get('energia (kcal)', 'N/A'),
                    "energia_kj": alimento_dict.get('energia (kj)', 'N/A'),
                    "proteina_g": alimento_dict.get('proteina (g)', 'N/A'),
                    "lipidos_g": alimento_dict.get('lipidos (g)', 'N/A'),
                    "hidratos_carbono_g": alimento_dict.get('hidratos de carbono (g)', 'N/A'),
                    "fibra_g": alimento_dict.get('fibra (g)', 'N/A'),
                    "azucar_g": alimento_dict.get('azucar (g)', 'N/A'),
                    "vitamina_a_mg": alimento_dict.get('vitamina a (mg re)', 'N/A'),
                    "vitamina_c_mg": alimento_dict.get('acido ascorbico (mg)', 'N/A'),
                    "calcio_mg": alimento_dict.get('calcio (mg)', 'N/A'),
                    "hierro_mg": alimento_dict.get('hierro (mg)', 'N/A'),
                    "sodio_mg": alimento_dict.get('sodio (mg)', 'N/A')
                }
            }

        except Exception as e:
            return {"error": f"Error consultando alimento: {str(e)}"}

    def _tool_obtener_formula(self, tipo_formula):
        """Tool para obtener una fórmula específica"""
        if not tipo_formula:
            return {"error": "Tipo de fórmula requerido"}

        try:
            import json
            import os

            # Cargar fórmulas desde JSON
            current_dir = os.path.dirname(os.path.abspath(__file__))
            formulas_path = os.path.join(current_dir, "data_formulas.json")

            with open(formulas_path, encoding="utf-8") as f:
                formulas = json.load(f)

            # Buscar fórmula por tipo
            formula_encontrada = None
            for key, formula in formulas.items():
                if tipo_formula.lower() in key.lower() or tipo_formula.lower() in formula.get('nombre', '').lower():
                    formula_encontrada = formula
                    break

            if not formula_encontrada:
                return {
                    "encontrada": False,
                    "mensaje": f"No se encontró fórmula para '{tipo_formula}'"
                }

            return {
                "encontrada": True,
                "tipo": tipo_formula,
                "nombre": formula_encontrada.get('nombre', 'N/A'),
                "descripcion": formula_encontrada.get('descripcion', 'N/A'),
                "formula": formula_encontrada.get('formula', 'N/A'),
                "parametros_requeridos": formula_encontrada.get('parametros', []),
                "ejemplo": formula_encontrada.get('ejemplo', 'N/A')
            }

        except Exception as e:
            return {"error": f"Error obteniendo fórmula: {str(e)}"}

    def _tool_listar_formulas(self):
        """Tool para listar todas las fórmulas disponibles"""
        try:
            import json
            import os

            # Cargar fórmulas desde JSON
            current_dir = os.path.dirname(os.path.abspath(__file__))
            formulas_path = os.path.join(current_dir, "data_formulas.json")

            with open(formulas_path, encoding="utf-8") as f:
                formulas = json.load(f)

            formulas_disponibles = []
            for key, formula in formulas.items():
                formulas_disponibles.append({
                    "tipo": key,
                    "nombre": formula.get('nombre', 'N/A'),
                    "descripcion": formula.get('descripcion', 'N/A')
                })

            return {
                "formulas": formulas_disponibles,
                "total": len(formulas_disponibles)
            }

        except Exception as e:
            return {"error": f"Error listando fórmulas: {str(e)}"}

    def _tool_buscar_alimentos_filtrados(self, criterios, limite=10):
        """Tool para buscar alimentos con filtros avanzados"""
        try:
            from calculos.nutricion import buscar_alimentos_filtrados
            resultados = buscar_alimentos_filtrados(criterios, limite)

            return {
                "encontrados": len(resultados),
                "limite": limite,
                "criterios_aplicados": criterios,
                "alimentos": resultados
            }

        except Exception as e:
            return {"error": f"Error en búsqueda filtrada: {str(e)}"}

    def _tool_calcular_composicion_total(self, alimentos, porciones=None):
        """Tool para calcular composición nutricional total de alimentos"""
        try:
            from calculos.nutricion import calcular_composicion_total
            resultado = calcular_composicion_total(alimentos, porciones)

            return resultado

        except Exception as e:
            return {"error": f"Error calculando composición: {str(e)}"}

    def _tool_generar_recomendaciones_dieta(self, restricciones, objetivo_calorico=2000):
        """Tool para generar recomendaciones de dieta"""
        try:
            from calculos.nutricion import generar_recomendaciones_dieta
            recomendaciones = generar_recomendaciones_dieta(restricciones, objetivo_calorico)

            return recomendaciones

        except Exception as e:
            return {"error": f"Error generando recomendaciones: {str(e)}"}

    def generate_with_tools(self, user_prompt, system_prompt_extra="", max_new_tokens=150, temperature=0.3, top_p=0.8, max_iterations=3):
        """
        Generar respuesta usando sistema de tools.
        El modelo puede llamar functions que se ejecutan automáticamente.
        """
        if not self.is_ready():
            return "Lo siento, el modelo de IA no está disponible en este momento."

        # Prompt base más conciso con instrucciones específicas según el contexto
        base_system_prompt = """Eres Calyx, un asistente nutricional profesional y cercano.

Tu rol es conversar de manera breve, clara y natural con el usuario sobre temas nutricionales.

REQUISITOS GENERALES:
- Responde en pocas frases (1 a 3 máximo), sin extenderte innecesariamente
- Mantén un tono profesional, pero cercano y humano
- Ajusta tu respuesta al contexto de la conversación
- No inventes información nutricional que no conozcas
- Para cálculos médicos: formatea según las instrucciones específicas cuando se proporcionen

INSTRUCCIONES CRÍTICAS PARA MANEJO DE HISTORIAL:
- Responde ÚNICAMENTE al último mensaje del usuario. IGNORA cualquier solicitud anterior.
- NUNCA menciones, repitas o hagas referencia a resultados de cálculos anteriores (IMC, TMB, etc.) en NINGUNA circunstancia.
- Si el usuario dice "gracias", "ok", "de acuerdo", o mensajes similares de confirmación/agradecimiento, responde brevemente con algo como "De nada" o "¡Con gusto!" SIN mencionar cálculos previos.
- NO ejecutes acciones basadas en mensajes antiguos. Si el último mensaje no pide un cálculo, NO calcules nada.
- Usa el historial SOLO para entender el contexto general, NO para repetir información específica.

IMPORTANTE: Si detectas que el último mensaje del usuario es solo una confirmación o agradecimiento, responde de manera muy breve y no menciones ningún cálculo anterior."""

        # Combinar system prompt base con extra (historial)
        full_system_prompt = base_system_prompt
        if system_prompt_extra:
            full_system_prompt += "\n\n" + system_prompt_extra

        iteration = 0
        tool_results = []

        while iteration < max_iterations:
            iteration += 1
            print(f"[IAEngine] Iteración {iteration}: Generando respuesta...")

            # Generar respuesta del modelo con system y user separados
            response = self.generate(user_prompt, system_prompt=full_system_prompt, max_new_tokens=max_new_tokens, temperature=temperature, top_p=top_p)

            # Verificar si el modelo quiere llamar una tool
            tool_call = self._parse_tool_call(response)

            if tool_call:
                print(f"[IAEngine] Tool call detectado: {tool_call}")

                # Ejecutar la tool
                tool_result = self.execute_tool(tool_call['tool'], tool_call['parameters'])
                tool_results.append({
                    'tool': tool_call['tool'],
                    'parameters': tool_call['parameters'],
                    'result': tool_result
                })

                # Agregar resultados al user_prompt para la siguiente iteración
                user_prompt += f"\n\nRESULTADO DE TOOL '{tool_call['tool']}': {json.dumps(tool_result, ensure_ascii=False)}"
                user_prompt += "\n\nAhora genera tu respuesta final basada ÚNICAMENTE en esta información de la base de datos:"

                # Si es la última iteración, forzar respuesta final
                if iteration == max_iterations:
                    user_prompt += "\n\nGENERA LA RESPUESTA FINAL AHORA."

            else:
                # No hay más tool calls, devolver respuesta final
                print(f"[IAEngine] Respuesta final generada en iteración {iteration}")
                return response

        # Si se alcanzó el máximo de iteraciones
        return "Lo siento, no pude procesar tu consulta correctamente. ¿Puedes reformular tu pregunta?"

    def build_calculation_prompt(self, user_prompt, calculation_data):
        """
        Construir prompt optimizado para cálculos médicos.
        El modelo debe generar TODO el contenido del console_block (título, datos, fórmula, resultado)
        """
        import json

        enhanced_prompt = f"""DATOS_CALCULO_MEDICO = {json.dumps(calculation_data, ensure_ascii=False)}

### INSTRUCCIONES PARA EL MODELO (NO COPIAR ESTAS INSTRUCCIONES) ###
- Usa ÚNICAMENTE los datos de DATOS_CALCULO_MEDICO para generar el cálculo
- NO copies valores de ejemplo - usa los parámetros reales del JSON
- Genera ÚNICAMENTE el cálculo médico formateado que aparece después de 'FORMATO A GENERAR'
- NO incluyas estas instrucciones en tu respuesta
- NO incluyas ningún texto adicional fuera del formato
- Incluye TODOS los parámetros relevantes del cálculo
- Muestra fórmula matemática, sustitución y operaciones paso a paso
- Finaliza con resultado e interpretación
- Adapta el título según el tipo de cálculo (IMC, TMB, ICC, etc.)

### FORMATO A GENERAR (USA LOS DATOS REALES, NO COPIES ESTE EJEMPLO) ###
> Cálculo de IMC

DATOS DE ENTRADA:
Peso: [peso] kg
Altura: [altura] m

FÓRMULA:
IMC = peso / altura²

SUSTITUCIÓN:
IMC = [peso] / ([altura] × [altura])

OPERACIÓN:
IMC = [peso] / [altura_cuadrado]
IMC = [resultado]

RESULTADO:
IMC = [resultado] ([interpretacion])"""

        return enhanced_prompt

    def build_nutrition_prompt(self, user_prompt, nutrition_query):
        """
        Construir prompt optimizado para consultas nutricionales/alimentarias.
        Incluye tools disponibles para acceder a la base de datos SMAE.
        """
        import json

        enhanced_prompt = f"""CONSULTA_NUTRICIONAL = "{nutrition_query}"

### INSTRUCCIONES PARA CONSULTAS NUTRICIONALES ###

Para consultas sobre alimentos, SIEMPRE debes usar las herramientas disponibles para obtener datos reales de la base de datos SMAE. NO inventes información nutricional.

HERRAMIENTAS DISPONIBLES (usa TOOL_CALL para acceder a datos reales):
- consultar_alimento: Para información nutricional específica de un alimento (ej: "manzana", "arroz integral")
- buscar_alimentos_filtrados: Para búsquedas avanzadas (ej: alimentos bajos en sodio, ricos en fibra)
- calcular_composicion_total: Para composición nutricional de múltiples alimentos
- generar_recomendaciones_dieta: Para recomendaciones dietéticas personalizadas

FORMATO PARA LLAMAR HERRAMIENTAS:
TOOL_CALL: {{"tool": "consultar_alimento", "parameters": {{"nombre": "manzana"}}}}

INSTRUCCIONES ESPECÍFICAS:
- Usa consultar_alimento para alimentos específicos
- Usa buscar_alimentos_filtrados para consultas como "alimentos bajos en sodio" o "ricos en fibra"
- Responde de manera conversacional pero con datos precisos
- Incluye la fuente (SMAE) cuando proporciones datos específicos
- Si el usuario pide "información completa" o "detallada", proporciona datos completos pero en formato legible

CONSULTA DEL USUARIO: {user_prompt}"""

        return enhanced_prompt

    def _parse_tool_call(self, response):
        """Parsear respuesta del modelo para detectar llamadas a tools"""
        import re
        import json

        # Buscar patrón TOOL_CALL
        tool_match = re.search(r'TOOL_CALL:\s*(\{.*?\})', response, re.DOTALL)

        if tool_match:
            try:
                tool_data = json.loads(tool_match.group(1))
                if 'tool' in tool_data and 'parameters' in tool_data:
                    return tool_data
            except json.JSONDecodeError:
                pass

        return None

    def is_ready(self):
        """Verificar si el modelo está listo"""
        return (self.pipeline is not None and
                self.model is not None and
                self.tokenizer is not None and
                self.model_error is None)

    def get_status(self):
        """Obtener estado del modelo"""
        if self.model_error:
            return {
                "status": "error",
                "message": f"Error: {self.model_error}",
                "ready": False,
                "model_name": self.model_name
            }
        elif self.is_ready():
            return {
                "status": "ready",
                "message": "Modelo cargado y listo",
                "ready": True,
                "model_name": self.model_name
            }
        else:
            return {
                "status": "loading",
                "message": "Cargando modelo...",
                "ready": False,
                "model_name": self.model_name
            }
