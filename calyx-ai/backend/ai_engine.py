
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

    def get_status(self):
        if self.model_error:
            return {"status": "error", "message": f"Modelo no disponible: {self.model_error}"}
        if self.is_ready():
            return {"status": "ok", "message": "Modelo cargado y listo"}
        return {"status": "loading", "message": "Modelo aún no está listo"}

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
