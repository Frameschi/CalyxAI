#!/usr/bin/env python3
"""
Script de debug para probar la carga del modelo Phi-3 sin FastAPI
"""

import torch
import traceback
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

def test_model_loading():
    model_name = "microsoft/phi-3-mini-4k-instruct"
    
    print(f"[DEBUG] torch.cuda.is_available(): {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"[DEBUG] GPU detectada: {torch.cuda.get_device_name(0)}")
    
    try:
        print("[DEBUG] Cargando tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        print("[DEBUG] Tokenizer cargado exitosamente")
        
        print("[DEBUG] Intentando cargar modelo...")
        
        if torch.cuda.is_available():
            try:
                import bitsandbytes as bnb
                print("[DEBUG] bitsandbytes disponible, probando carga 4-bit...")
                
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
                
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    quantization_config=quantization_config,
                    device_map="auto",
                    trust_remote_code=True
                )
                print("[DEBUG] ✅ Modelo cargado exitosamente con 4-bit!")
                
            except Exception as e:
                print(f"[DEBUG] ❌ Error con 4-bit: {e}")
                print("[DEBUG] Probando FP16...")
                
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    trust_remote_code=True
                )
                print("[DEBUG] ✅ Modelo cargado exitosamente con FP16!")
        else:
            print("[DEBUG] No GPU, cargando en CPU...")
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16,
                device_map="cpu",
                trust_remote_code=True
            )
            print("[DEBUG] ✅ Modelo cargado exitosamente en CPU!")
            
        # Prueba rápida de generación
        print("[DEBUG] Probando generación...")
        test_input = tokenizer("Hola", return_tensors="pt")
        if torch.cuda.is_available():
            test_input = {k: v.cuda() for k, v in test_input.items()}
            
        with torch.no_grad():
            output = model.generate(
                test_input['input_ids'],
                max_length=10,
                do_sample=False,
                # CRÍTICO: Configuración para evitar error DynamicCache
                past_key_values=None,  # Forzar no usar cache
                use_cache=False,  # Deshabilitar cache completamente
                pad_token_id=tokenizer.eos_token_id  # Configurar pad_token_id
            )
        
        result = tokenizer.decode(output[0], skip_special_tokens=True)
        print(f"[DEBUG] ✅ Generación exitosa: {result}")
        
    except Exception as e:
        print(f"[DEBUG] ❌ Error fatal: {e}")
        print(f"[DEBUG] Traceback completo:")
        traceback.print_exc()

if __name__ == "__main__":
    test_model_loading()
