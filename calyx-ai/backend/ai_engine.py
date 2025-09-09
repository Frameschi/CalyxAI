
from transformers import AutoModelForCausalLM, AutoTokenizer, logging, BitsAndBytesConfig
import torch
import os
import ollama

class IAEngine:
    def __init__(self, model_name=None):
        # Configuración de modelos disponibles
        self.available_models = {
            "phi3-mini": {
                "name": "microsoft/phi-3-mini-4k-instruct",
                "engine": "huggingface",
                "description": "Phi-3 Mini - Rápido y eficiente"
            },
            "deepseek-r1": {
                "name": "hf.co/unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF:Q4_K_M",
                "engine": "ollama", 
                "description": "DeepSeek-R1 - Razonamiento matemático avanzado"
            }
        }
        
        # Modelo por defecto
        self.current_model_key = "phi3-mini"
        current_model_config = self.available_models[self.current_model_key]
        self.model_name = model_name or current_model_config["name"]
        self.current_engine = current_model_config["engine"]
        
        # Engines
        self.tokenizer = None
        self.model = None
        self.model_error = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.ollama_client = None
        
        self._load_model()

    def _get_fallback_message(self):
        """Obtiene mensaje de fallback según el modelo activo"""
        if self.current_model_key == 'deepseek-r1':
            return "🧬 DeepSeek Nutrición Avanzada activado. Capacidad de análisis profundo y razonamiento nutricional disponible. ¿Qué consulta nutricional puedo analizar para ti?"
        else:
            return "¡Hola! Soy CalyxAI, tu asistente nutricional. ¿En qué puedo ayudarte hoy?"

    def _load_model(self):
        if self.current_engine == "huggingface":
            self._load_huggingface_model()
        elif self.current_engine == "ollama":
            self._load_ollama_model()
        else:
            self.model_error = f"Engine no soportado: {self.current_engine}"

    def _load_huggingface_model(self):
        logging.set_verbosity_info()
        print(f"[IAEngine] Cargando modelo HuggingFace: {self.model_name}")
        print(f"[IAEngine] torch.cuda.is_available(): {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"[IAEngine] GPU detectada: {torch.cuda.get_device_name(0)}")
        else:
            print("[IAEngine] No se detectó GPU, usando CPU (puede ser muy lento o fallar por RAM)")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Configuración explícita para GPU con 4-bit optimizada
            if torch.cuda.is_available():
                try:
                    import bitsandbytes as bnb
                    print("[IAEngine] bitsandbytes detectado, cargando modelo en GPU 4-bit optimizada...")
                    
                    # Configuración optimizada para velocidad en GPU
                    quantization_config = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_use_double_quant=False,  # Deshabilitado para mejor velocidad
                        bnb_4bit_quant_type="nf4"
                    )
                    
                    # Intento 1: Configuración optimizada para velocidad
                    try:
                        self.model = AutoModelForCausalLM.from_pretrained(
                            self.model_name,
                            quantization_config=quantization_config,
                            device_map={"": 0},  # Forzar GPU 0
                            torch_dtype=torch.float16,
                            trust_remote_code=True,
                            low_cpu_mem_usage=True,
                            attn_implementation="eager"  # Usar implementación estándar más rápida
                        )
                        print("[IAEngine] Modelo cargado en GPU con 4-bit cuantización optimizada para velocidad.")
                        
                        # Verificación crítica de ubicación del modelo
                        if hasattr(self.model, 'device'):
                            print(f"[IAEngine] ✅ Modelo ubicado en: {self.model.device}")
                        if hasattr(self.model, 'hf_device_map'):
                            print(f"[IAEngine] ✅ Device map: {self.model.hf_device_map}")
                        
                        # Test rápido de GPU
                        try:
                            test_input = self.tokenizer("Test", return_tensors="pt").to(self.model.device)
                            with torch.no_grad():
                                test_output = self.model(**test_input)
                            print("[IAEngine] ✅ Test de GPU exitoso - modelo funcionando en GPU")
                        except Exception as test_error:
                            print(f"[IAEngine] ⚠️ Error en test de GPU: {test_error}")
                            
                    except Exception as opt_error:
                        print(f"[IAEngine] Error con configuración optimizada: {opt_error}")
                        print("[IAEngine] Intentando configuración básica...")
                        
                        # Intento 2: Configuración básica simplificada
                        self.model = AutoModelForCausalLM.from_pretrained(
                            self.model_name,
                            quantization_config=quantization_config,
                            device_map="auto",  # Dejar que PyTorch decida automáticamente
                            torch_dtype=torch.float16,
                            trust_remote_code=True
                        )
                        print("[IAEngine] Modelo cargado en GPU con configuración básica.")
                        
                except ImportError:
                    print("[IAEngine] bitsandbytes no disponible, cargando en GPU FP16...")
                    # Configuración de fallback sin cuantización
                    try:
                        self.model = AutoModelForCausalLM.from_pretrained(
                            self.model_name,
                            torch_dtype=torch.float16,
                            device_map="auto",
                            trust_remote_code=True
                        )
                        print("[IAEngine] Modelo cargado en GPU FP16.")
                    except Exception as fp16_error:
                        print(f"[IAEngine] Error en GPU FP16: {fp16_error}")
                        print("[IAEngine] Intentando carga en CPU como último recurso...")
                        raise fp16_error  # Propagar el error para que caiga al bloque CPU
            else:
                print("[IAEngine] GPU no disponible, usando CPU...")
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16,
                    device_map="cpu",
                    trust_remote_code=True
                )
                print("[IAEngine] Modelo cargado en CPU.")
        except Exception as e:
            self.model_error = str(e)
            print(f"[IAEngine] Error al cargar el modelo HuggingFace: {self.model_error}")

    def _load_ollama_model(self):
        print(f"[IAEngine] 🔥 FORZANDO DeepSeek-R1 AL MÁXIMO EN GPU: {self.model_name}")
        try:
            # CONFIGURACIÓN ULTRA AGRESIVA PARA GPU - SIN LÍMITES
            import os
            os.environ['OLLAMA_NUM_GPU'] = '1'  # Usar 1 GPU
            os.environ['OLLAMA_GPU_FRACTION'] = '0.98'  # 98% de la GPU  
            os.environ['OLLAMA_NUM_GPU_LAYERS'] = '999'  # TODAS LAS CAPAS EN GPU
            os.environ['OLLAMA_MEMORY'] = '8GB'  # Usar toda la memoria disponible
            os.environ['OLLAMA_LOW_VRAM'] = 'false'  # NO limitar VRAM
            
            print("[IAEngine] 🚀 Variables GPU AGRESIVAS configuradas:")
            print(f"[IAEngine] 🔥 OLLAMA_NUM_GPU_LAYERS = 999 (TODAS)")
            print(f"[IAEngine] 🔥 OLLAMA_GPU_FRACTION = 0.98 (98%)")
            
            self.ollama_client = ollama.Client()
            
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
                    print(f"[IAEngine] ✅ Modelo {self.model_name} ya disponible")
                
                # Test del modelo CON CONFIGURACIÓN ULTRA AGRESIVA
                print("[IAEngine] 🔥 Probando configuración GPU ULTRA AGRESIVA...")
                test_response = self.ollama_client.chat(
                    model=self.model_name,
                    messages=[{'role': 'user', 'content': 'GPU Test'}],
                    options={
                        'num_predict': 5,
                        'num_gpu': 1,           # FORZAR GPU
                        'num_thread': 1,        # MÍNIMO CPU (solo 1 thread)
                        'num_ctx': 2048,        # Contexto optimizado
                        'low_vram': False,      # SIN límites VRAM
                        'numa': False,          # Sin NUMA
                        'use_mlock': True,      # Lock memoria
                        'use_mmap': True        # Memory mapping
                    }
                )
                print("[IAEngine] Cliente Ollama inicializado correctamente")
                
            except Exception as e:
                self.model_error = f"Error al verificar/descargar modelo Ollama: {str(e)}"
                print(f"[IAEngine] {self.model_error}")
                
        except Exception as e:
            self.model_error = f"Error al conectar con Ollama: {str(e)}"
            print(f"[IAEngine] {self.model_error}")

    def is_ready(self):
        if self.current_engine == "huggingface":
            return self.model is not None and self.tokenizer is not None and self.model_error is None
        elif self.current_engine == "ollama":
            return self.ollama_client is not None and self.model_error is None
        return False

    def is_model_downloaded(self):
        """Verificar si el modelo está descargado en el cache local"""
        try:
            from transformers import AutoTokenizer
            # Intentar cargar solo el tokenizer para verificar si el modelo existe
            tokenizer_path = AutoTokenizer.from_pretrained(
                self.model_name, 
                local_files_only=True
            )
            return True
        except Exception:
            return False

    def get_model_cache_info(self):
        """Obtener información sobre el cache del modelo"""
        try:
            import os
            from pathlib import Path
            
            # Directorio típico de cache de HuggingFace
            cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
            model_cache_path = None
            model_size = 0
            
            if os.path.exists(cache_dir):
                for item in os.listdir(cache_dir):
                    if "phi-3" in item.lower():
                        model_path = os.path.join(cache_dir, item)
                        if os.path.isdir(model_path):
                            model_cache_path = model_path
                            # Calcular tamaño del modelo
                            for root, dirs, files in os.walk(model_path):
                                for file in files:
                                    model_size += os.path.getsize(os.path.join(root, file))
                            break
            
            return {
                "cache_path": model_cache_path,
                "size_mb": round(model_size / (1024 * 1024), 2) if model_size > 0 else 0,
                "is_downloaded": model_cache_path is not None
            }
        except Exception as e:
            return {
                "cache_path": None,
                "size_mb": 0,
                "is_downloaded": False,
                "error": str(e)
            }

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
        Generación optimizada para asistente nutricional usando el engine apropiado
        """
        if not self.is_ready():
            raise RuntimeError("El modelo no está listo o falló la carga.")
        
        if self.current_engine == "huggingface":
            return self._generate_huggingface(prompt, max_new_tokens, temperature)
        elif self.current_engine == "ollama":
            return self._generate_ollama(prompt, max_new_tokens, temperature)
        else:
            raise RuntimeError(f"Engine no soportado: {self.current_engine}")

    def _generate_huggingface(self, prompt, max_new_tokens=120, temperature=0.3):
        """Generación usando HuggingFace (Phi-3)"""
        import threading
        import time
        
        # Variable para almacenar resultado
        result = {"response": None, "error": None}
        
        def generate_with_timeout():
            try:
                inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=max_new_tokens,
                        do_sample=True,
                        temperature=temperature,
                        top_p=0.9,  # Más selectivo en las opciones
                        top_k=50,   # Mayor diversidad controlada  
                        repetition_penalty=1.1,  # Reducido para mejor velocidad
                        no_repeat_ngram_size=2,   # Reducido para mejor velocidad
                        use_cache=True,  # CRÍTICO: Habilitar caché KV para usar GPU eficientemente
                        pad_token_id=self.tokenizer.eos_token_id
                    )
                result["response"] = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            except Exception as e:
                result["error"] = str(e)
        
        # Ejecutar generación en thread separado
        thread = threading.Thread(target=generate_with_timeout)
        thread.daemon = True
        thread.start()
        thread.join(timeout=30)  # Reducido a 30 segundos para forzar eficiencia GPU
        
        # Si el thread aún está vivo, significa que está siendo muy lento
        if thread.is_alive():
            print("[IAEngine] Timeout después de 30 segundos - posible problema de GPU")
            response = self._get_fallback_message()
        elif result["error"]:
            print(f"[IAEngine] Error en generación: {result['error']}")
            response = self._get_fallback_message()
        else:
            response = result["response"]
        
        # Limpiar respuesta: eliminar eco del prompt si lo hay
        if response.lower().startswith(prompt.lower()):
            response = response[len(prompt):].lstrip("\n :.-")
        # Limitar a 3 líneas para mayor naturalidad
        response = "\n".join(response.splitlines()[:3]).strip()
        return response

    def _generate_ollama(self, prompt, max_new_tokens=300, temperature=0.3):
        """Generación usando Ollama (DeepSeek-R1) 🔥 ULTRA AGRESIVO PARA GPU"""
        try:
            # CONFIGURACIÓN ULTRA AGRESIVA - 99% GPU, 1% CPU
            options = {
                'num_predict': max(400, max_new_tokens),  # Suficiente para respuestas completas
                'temperature': 0.2,  # Más determinístico, menos divagación
                'top_p': 0.8,        # Más enfocado en tokens relevantes
                'top_k': 30,         # Vocabulario más restringido
                'repeat_penalty': 1.1,  # Evitar repeticiones
                'stop': ['Usuario:', 'Pregunta:', '\n\nUsuario:', 'user:', '\nuser:'],  # Solo stop en cambios de turno
                # 🔥🔥🔥 CONFIGURACIONES ULTRA AGRESIVAS PARA GPU 🔥🔥🔥
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
            
            print(f"[IAEngine] 🔥🔥🔥 GENERANDO CON GPU AL MÁXIMO - DeepSeek-R1 ULTRA AGRESIVO, prompt length: {len(prompt)}")
            print(f"[IAEngine] 🚀 Configuración: 999 capas GPU, 1 thread CPU, sin límites VRAM")
            
            response = self.ollama_client.chat(
                model=self.model_name,
                messages=[
                    {'role': 'user', 'content': prompt}
                ],
                options=options
            )
            
            # Extraer el contenido completo de la respuesta
            message_content = response.get('message', {}).get('content', '')
            print(f"[IAEngine] 🔥✅ RESPUESTA GPU ULTRA AGRESIVA RECIBIDA, length: {len(message_content)}")
            
            # NO limitar líneas para DeepSeek-R1 - permitir respuestas completas
            return message_content.strip()
            
        except Exception as e:
            print(f"[IAEngine] ❌ Error en generación GPU ULTRA AGRESIVA: {e}")
            return self._get_fallback_message()

    def switch_model(self, model_key):
        """Cambiar entre modelos disponibles"""
        if model_key not in self.available_models:
            raise ValueError(f"Modelo '{model_key}' no disponible. Opciones: {list(self.available_models.keys())}")
        
        if model_key == self.current_model_key:
            print(f"[IAEngine] Modelo '{model_key}' ya está cargado")
            return True
        
        print(f"[IAEngine] Cambiando de '{self.current_model_key}' a '{model_key}'...")
        
        # Limpiar modelo actual de memoria
        if self.current_engine == "huggingface" and self.model is not None:
            del self.model
            del self.tokenizer
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        elif self.current_engine == "ollama":
            self.ollama_client = None
        
        # Configurar nuevo modelo
        new_model_config = self.available_models[model_key]
        self.current_model_key = model_key
        self.model_name = new_model_config["name"]
        self.current_engine = new_model_config["engine"]
        
        # Reset variables
        self.model = None
        self.tokenizer = None
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
