
from transformers import AutoModelForCausalLM, AutoTokenizer, logging
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
            # Intentar cargar en 4-bit si bitsandbytes está disponible
            try:
                import bitsandbytes as bnb
                print("[IAEngine] bitsandbytes detectado, intentando cargar modelo en 4-bit...")
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    load_in_4bit=True,
                    device_map="auto"
                )
                print("[IAEngine] Modelo cargado en 4-bit.")
            except ImportError:
                print("[IAEngine] bitsandbytes no disponible, cargando modelo en FP16...")
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16,
                    device_map="auto"
                )
                print("[IAEngine] Modelo cargado en FP16.")
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

    def generate(self, prompt, max_new_tokens=80, temperature=0.5):
        """
        Generación profesional: respuestas más breves, naturales y menos propensas a alucinaciones.
        - max_new_tokens=80: Limita la longitud de la respuesta.
        - temperature=0.5: Menos creatividad, más precisión.
        """
        if not self.is_ready():
            raise RuntimeError("El modelo no está listo o falló la carga.")
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=temperature,
                top_p=0.95,
                top_k=40,
                repetition_penalty=1.1
            )
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Limpiar respuesta: eliminar eco del prompt si lo hay
        if response.lower().startswith(prompt.lower()):
            response = response[len(prompt):].lstrip("\n :.-")
        # Limitar a 3 líneas para mayor naturalidad
        response = "\n".join(response.splitlines()[:3]).strip()
        return response
