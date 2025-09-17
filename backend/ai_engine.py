# Imports para DeepSeek-R1 via Ollama
import os
import ollama

class IAEngine:
    def __init__(self, model_name=None):
        # Configuración de modelos disponibles - SOLO DEEPSEEK-R1
        self.available_models = {
            "deepseek-r1": {
                "name": "hf.co/unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF:Q4_K_M",
                "engine": "ollama", 
                "description": "DeepSeek-R1 - Razonamiento matemático avanzado"
            }
        }
        
        # Modelo por defecto - DeepSeek-R1
        self.current_model_key = "deepseek-r1"
        current_model_config = self.available_models[self.current_model_key]
        self.model_name = model_name or current_model_config["name"]
        self.current_engine = current_model_config["engine"]
        
        # Engines
        self.model_error = None
        self.ollama_client = None
        
        self._load_model()

    def _load_model(self):
        """Cargar solo DeepSeek-R1 via Ollama"""
        if self.current_engine == "ollama":
            self._load_ollama_model()
        else:
            self.model_error = f"Engine no soportado: {self.current_engine}. Solo se soporta Ollama con DeepSeek-R1."

    def _load_ollama_model(self):
        print(f"[IAEngine] [LOADING] Configurando DeepSeek-R1 con optimización GPU: {self.model_name}")
        try:
            # CONFIGURACIÓN OPTIMIZADA PARA GPU - BALANCEADA
            import os
            os.environ['OLLAMA_NUM_GPU'] = '1'  # Usar 1 GPU
            os.environ['OLLAMA_GPU_FRACTION'] = '0.8'  # 80% de la GPU (más estable)
            os.environ['OLLAMA_NUM_GPU_LAYERS'] = '32'  # Capas optimizadas
            os.environ['OLLAMA_LOW_VRAM'] = 'false'  # NO limitar VRAM

            print("[IAEngine] [CONFIG] Variables GPU optimizadas configuradas:")
            print(f"[IAEngine] [LOADING] OLLAMA_NUM_GPU_LAYERS = 32")
            print(f"[IAEngine] [LOADING] OLLAMA_GPU_FRACTION = 0.8 (80%)")

            # Intentar conectar con diferentes configuraciones de host
            host_options = ['http://localhost:11434', None]  # None usa default

            for host in host_options:
                try:
                    if host:
                        self.ollama_client = ollama.Client(host=host)
                        print(f"[IAEngine] [CONNECT] Intentando conectar a Ollama en: {host}")
                    else:
                        self.ollama_client = ollama.Client()
                        print(f"[IAEngine] [CONNECT] Usando configuración por defecto de Ollama")

                    # Verificar conexión listando modelos
                    models = self.ollama_client.list()
                    print(f"[IAEngine] [OK] Conexión exitosa. Modelos disponibles: {len(models.models)}")
                    break

                except Exception as conn_error:
                    print(f"[IAEngine] [ERROR] Error de conexión con host {host}: {conn_error}")
                    if host == host_options[-1]:  # Último intento
                        self.model_error = f"Error de conexión con Ollama: {conn_error}"
                        print(f"[IAEngine] [FALLBACK] Usando modo fallback sin modelo")
                        return
            
            # Verificar si el modelo está disponible
            try:
                models = self.ollama_client.list()
                model_names = [model.model for model in models.models]
                
                if self.model_name not in model_names:
                    print(f"[IAEngine] Modelo {self.model_name} no encontrado. Intentando descarga...")
                    print("[IAEngine] Esto puede tomar varios minutos...")
                    self.ollama_client.pull(self.model_name)
                    print(f"[IAEngine] Modelo {self.model_name} descargado exitosamente")
                else:
                    print(f"[IAEngine] [OK] Modelo {self.model_name} ya disponible")
                
                # Test del modelo con configuración optimizada
                print("[IAEngine] [TEST] Probando configuración GPU optimizada...")
                test_response = self.ollama_client.chat(
                    model=self.model_name,
                    messages=[{'role': 'user', 'content': 'Test de funcionamiento básico'}],
                    options={
                        'num_predict': 10,
                        'num_gpu': 1,           # Usar GPU
                        'num_thread': 4,        # Threads balanceados
                        'num_ctx': 4096,        # Contexto ampliado para nutrición
                        'temperature': 0.1,     # Baja temperatura para respuestas consistentes
                        'low_vram': False
                    }
                )
                print("[IAEngine] [OK] Cliente Ollama inicializado correctamente")
                print(f"[IAEngine] 📝 Respuesta de test: {test_response['message']['content'][:100]}...")
                
            except Exception as e:
                self.model_error = f"Error al verificar/descargar modelo Ollama: {str(e)}"
                print(f"[IAEngine] {self.model_error}")
                
        except Exception as e:
            self.model_error = f"Error al conectar con Ollama: {str(e)}"
            print(f"[IAEngine] {self.model_error}")

    def is_ready(self):
        """Verificar si DeepSeek-R1 está listo via Ollama"""
        if self.current_engine == "ollama":
            return self.ollama_client is not None and self.model_error is None
        return False

    def is_model_downloaded(self):
        """Verificar si el modelo DeepSeek-R1 está descargado en Ollama"""
        if self.ollama_client is None:
            return False
        try:
            models = self.ollama_client.list()
            model_names = [model.model for model in models.models]
            return self.model_name in model_names
        except Exception:
            return False

    def get_model_cache_info(self):
        """Obtener información sobre el modelo en Ollama"""
        try:
            if self.ollama_client is None:
                return {"error": "Cliente Ollama no disponible"}
            
            models = self.ollama_client.list()
            for model in models.models:
                if model.model == self.model_name:
                    return {
                        "model": model.model,
                        "size": getattr(model, 'size', 'Desconocido'),
                        "modified_at": getattr(model, 'modified_at', 'Desconocido'),
                        "engine": "Ollama"
                    }
            return {"error": f"Modelo {self.model_name} no encontrado"}
        except Exception as e:
            return {"error": str(e)}

    def get_status(self):
        cache_info = self.get_model_cache_info()
        
        status_info = {
            "model_name": self.model_name,
            "device": self.device,
            "is_downloaded": cache_info["is_downloaded"],
            "cache_size_mb": cache_info["size_mb"],
            "cache_path": cache_info["cache_path"]
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
                "message": "Modelo cargado y listo",
                "ready": True
            })
        elif cache_info["is_downloaded"]:
            status_info.update({
                "status": "loading", 
                "message": "Modelo descargado, cargando en memoria...",
                "ready": False
            })
        else:
            status_info.update({
                "status": "not_downloaded", 
                "message": "Modelo no descargado. Se descargará en el primer uso.",
                "ready": False
            })
        
        return status_info

    def generate(self, prompt, max_new_tokens=120, temperature=0.3):
        """
        Generación usando DeepSeek-R1 via Ollama
        """
        if not self.is_ready():
            raise RuntimeError("DeepSeek-R1 no está disponible. Verifica que Ollama esté corriendo y el modelo esté descargado.")
        
        if self.current_engine == "ollama":
            return self._generate_ollama(prompt, max_new_tokens, temperature)
        else:
            raise RuntimeError(f"Engine no soportado: {self.current_engine}. Solo se soporta Ollama con DeepSeek-R1.")

    def _generate_ollama(self, prompt, max_new_tokens=300, temperature=0.3):
        """Generación usando Ollama (DeepSeek-R1) [HOT] ULTRA AGRESIVO PARA GPU"""
        try:
            # CONFIGURACIÓN ULTRA AGRESIVA - 99% GPU, 1% CPU
            options = {
                'num_predict': max(400, max_new_tokens),  # Suficiente para respuestas completas
                'temperature': 0.2,  # Más determinístico, menos divagación
                'top_p': 0.8,        # Más enfocado en tokens relevantes
                'top_k': 30,         # Vocabulario más restringido
                'repeat_penalty': 1.1,  # Evitar repeticiones
                'stop': ['Usuario:', 'Pregunta:', '\n\nUsuario:', 'user:', '\nuser:'],  # Solo stop en cambios de turno
                # [HOT][HOT][HOT] CONFIGURACIONES ULTRA AGRESIVAS PARA GPU [HOT][HOT][HOT]
                'num_gpu': 1,           # FORZAR GPU AL 100%
                'num_thread': 1,        # SOLO 1 THREAD CPU (MÍNIMO)
                'numa': False,          # Sin NUMA para GPU
                'use_mlock': True,      # Lock memoria AGRESIVO
                'low_vram': False,      # SIN LÍMITES DE VRAM
                'use_mmap': True,       # Memory mapping optimizado
                'num_ctx': 4096,        # Contexto completo
                'num_batch': 512,       # Batch grande para GPU
                'num_gqa': 8,          # Group Query Attention optimizado
                'num_gpu_layers': 999,  # TODAS LAS CAPAS EN GPU
                'main_gpu': 0,         # GPU primaria
                'tensor_split': None    # No dividir tensores
            }
            
            print(f"[IAEngine] [HOT][HOT][HOT] GENERANDO CON GPU AL MÁXIMO - DeepSeek-R1 ULTRA AGRESIVO, prompt length: {len(prompt)}")
            print(f"[IAEngine] [STARTUP] Configuración: 999 capas GPU, 1 thread CPU, sin límites VRAM")
            
            response = self.ollama_client.chat(
                model=self.model_name,
                messages=[
                    {'role': 'user', 'content': prompt}
                ],
                options=options
            )
            
            # Extraer el contenido completo de la respuesta
            message_content = response.get('message', {}).get('content', '')
            print(f"[IAEngine] [HOT][OK] RESPUESTA GPU ULTRA AGRESIVA RECIBIDA, length: {len(message_content)}")
            
            # NO limitar líneas para DeepSeek-R1 - permitir respuestas completas
            return message_content.strip()
            
        except Exception as e:
            print(f"[IAEngine] [ERROR] Error en generación GPU ULTRA AGRESIVA: {e}")
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
        if self.current_engine == "ollama":
            self.ollama_client = None
        
        # Configurar nuevo modelo
        new_model_config = self.available_models[model_key]
        self.current_model_key = model_key
        self.model_name = new_model_config["name"]
        self.current_engine = new_model_config["engine"]
        
        # Reset variables
        self.ollama_client = None
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

    def generate_with_tools(self, prompt, max_new_tokens=150, temperature=0.3, max_iterations=3):
        """
        Generar respuesta usando sistema de tools.
        El modelo puede llamar functions que se ejecutan automáticamente.
        """
        if not self.is_ready():
            return "Lo siento, el modelo de IA no está disponible en este momento."

        # Prompt base más conciso con instrucciones estrictas sobre uso de BD
        system_prompt = """Eres un asistente nutricional. SIEMPRE usa las bases de datos como fuente única de verdad.

REGLAS:
1. NUNCA uses conocimiento preentrenado para datos nutricionales
2. Para alimentos: llama TOOL_CALL: {"tool": "consultar_alimento", "parameters": {"nombre": "nombre_alimento"}}
3. Para fórmulas: llama TOOL_CALL: {"tool": "obtener_formula", "parameters": {"tipo": "tipo_formula"}}

Después de resultados, genera respuesta final."""

        full_prompt = f"{system_prompt}\n\nConsulta del usuario: {prompt}"

        iteration = 0
        tool_results = []

        while iteration < max_iterations:
            iteration += 1
            print(f"[IAEngine] Iteración {iteration}: Generando respuesta...")

            # Generar respuesta del modelo
            response = self.generate(full_prompt, max_new_tokens=max_new_tokens, temperature=temperature)

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

                # Agregar resultados al prompt para la siguiente iteración
                full_prompt += f"\n\nRESULTADO DE TOOL '{tool_call['tool']}': {json.dumps(tool_result, ensure_ascii=False)}"
                full_prompt += "\n\nAhora genera tu respuesta final basada ÚNICAMENTE en esta información de la base de datos:"

                # Si es la última iteración, forzar respuesta final
                if iteration == max_iterations:
                    full_prompt += "\n\nGENERA LA RESPUESTA FINAL AHORA."

            else:
                # No hay más tool calls, devolver respuesta final
                print(f"[IAEngine] Respuesta final generada en iteración {iteration}")
                return response

        # Si se alcanzó el máximo de iteraciones
        return "Lo siento, no pude procesar tu consulta correctamente. ¿Puedes reformular tu pregunta?"

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
