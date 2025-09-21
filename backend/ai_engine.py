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
- Para consultas sobre alimentos: usa TOOL_CALL cuando necesites datos específicos
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
        Centraliza toda la lógica de formateo de cálculos en ai_engine.py
        """
        import json

        enhanced_prompt = f"""INSTRUCCIONES PARA FORMATEAR CÁLCULO MÉDICO:

DATOS_CALCULO_MEDICO = {json.dumps(calculation_data, ensure_ascii=False)}

GENERA ÚNICAMENTE el desglose del cálculo médico en formato profesional y estructurado.

FORMATO GENERAL A SEGUIR:
- Título descriptivo con el nombre del cálculo
- Datos de entrada claramente listados
- Fórmula matemática utilizada
- Operación paso a paso del cálculo
- Resultado final con unidades e interpretación
- Cada sección claramente separada y etiquetada

EJEMPLO PARA IMC:
> Cálculo de IMC

DATOS DE ENTRADA:
Peso: 65.0 kg
Altura: 1.75 m

FÓRMULA:
IMC = peso / altura²

SUSTITUCIÓN:
IMC = 65.0 / (1.75 × 1.75)

OPERACIÓN:
IMC = 65.0 / 3.0625
IMC = 21.2

RESULTADO:
IMC = 21.2 (Normal)

IMPORTANTE:
- Adapta el formato según el tipo de cálculo (IMC, TMB, ICC, etc.)
- Mantén consistencia profesional
- Incluye todos los parámetros relevantes
- Muestra los cálculos paso a paso
- Finaliza con resultado e interpretación"""

        return enhanced_prompt

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
