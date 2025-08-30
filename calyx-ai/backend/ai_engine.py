
from transformers import AutoModelForCausalLM, AutoTokenizer, logging, BitsAndBytesConfig
import torch
import os

class IAEngine:
    def __init__(self, model_name=None):
        self.model_name = model_name or os.getenv("PHI3_MODEL_NAME", "microsoft/phi-3-mini-4k-instruct")
        self.tokenizer = None
        self.model = None
        self.model_error = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._load_model()

    def _load_model(self):
        logging.set_verbosity_info()
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
                    
                    # Configuración simplificada y más conservadora
                    quantization_config = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_use_double_quant=True,
                        bnb_4bit_quant_type="nf4"
                    )
                    
                    # Intento 1: Configuración optimizada
                    try:
                        self.model = AutoModelForCausalLM.from_pretrained(
                            self.model_name,
                            quantization_config=quantization_config,
                            device_map={"": 0},
                            torch_dtype=torch.float16,
                            trust_remote_code=True,
                            low_cpu_mem_usage=True
                        )
                        print("[IAEngine] Modelo cargado en GPU con 4-bit cuantización optimizada.")
                    except Exception as opt_error:
                        print(f"[IAEngine] Error con configuración optimizada: {opt_error}")
                        print("[IAEngine] Intentando configuración básica...")
                        
                        # Intento 2: Configuración básica sin optimizaciones avanzadas
                        self.model = AutoModelForCausalLM.from_pretrained(
                            self.model_name,
                            quantization_config=quantization_config,
                            device_map="auto",  # Dejar que PyTorch decida automáticamente
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
            print(f"[IAEngine] Error al cargar el modelo: {self.model_error}")

    def is_ready(self):
        return self.model is not None and self.tokenizer is not None and self.model_error is None

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
        Generación optimizada para asistente nutricional:
        - max_new_tokens=120: Respuestas más completas pero concisas
        - temperature=0.3: Más consistente, menos aleatoriedad
        - timeout=15s: Más tiempo para respuestas de calidad
        """
        import threading
        import time
        
        if not self.is_ready():
            raise RuntimeError("El modelo no está listo o falló la carga.")
        
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
                        repetition_penalty=1.2,  # Evita más repeticiones
                        no_repeat_ngram_size=3,   # Evita repetir frases de 3 palabras
                        use_cache=False,  # Fix DynamicCache.seen_tokens error
                        pad_token_id=self.tokenizer.eos_token_id  # Fix padding issues
                    )
                result["response"] = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            except Exception as e:
                result["error"] = str(e)
        
        # Ejecutar generación en thread separado
        thread = threading.Thread(target=generate_with_timeout)
        thread.daemon = True
        thread.start()
        thread.join(timeout=15)  # 15 segundos timeout para mejores respuestas
        
        # Si el thread aún está vivo, significa que se colgó
        if thread.is_alive():
            print("[IAEngine] Timeout - usando respuesta fallback")
            response = "¡Hola! Soy CalyxAI, tu asistente nutricional. ¿En qué puedo ayudarte hoy?"
        elif result["error"]:
            print(f"[IAEngine] Error en generación: {result['error']}")
            response = "¡Hola! Soy CalyxAI, tu asistente nutricional. ¿En qué puedo ayudarte hoy?"
        else:
            response = result["response"]
        # Limpiar respuesta: eliminar eco del prompt si lo hay
        if response.lower().startswith(prompt.lower()):
            response = response[len(prompt):].lstrip("\n :.-")
        # Limitar a 3 líneas para mayor naturalidad
        response = "\n".join(response.splitlines()[:3]).strip()
        return response
