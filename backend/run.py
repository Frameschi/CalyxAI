#!/usr/bin/env python3
"""Script para ejecutar modelos como ollama run model_name"""
import os
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
import sys
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
def load_model(model_name):
    print(f"Cargando {model_name}...")
    if model_name == "qwen2.5-3b":
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )
        print("Usando cuantizacion 4-bit para Qwen2.5-3B")
        full_model_name = "Qwen/Qwen2.5-3B-Instruct"
    else:
        print(f"Modelo '{model_name}' no soportado. Solo disponible: qwen2.5-3b")
        return None, None
    
    tokenizer = AutoTokenizer.from_pretrained(full_model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        full_model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.float16
    )
    return tokenizer, model
def chat_loop(tokenizer, model, model_name):
    print(f"{model_name} listo! Escribe tus mensajes (Ctrl+C para salir)")
    print("=" * 50)
    while True:
        try:
            user_input = input(">>> ").strip()
            if not user_input: continue
            messages = [{"role": "user", "content": user_input}]
            input_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
            print("Generando respuesta...")
            with torch.no_grad():
                outputs = model.generate(**inputs, max_new_tokens=512, temperature=0.7, do_sample=True, pad_token_id=tokenizer.eos_token_id)
            response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
            print(f"AI: {response}")
            print()
        except KeyboardInterrupt:
            print("\nHasta luego!")
            break
        except Exception as e:
            print(f"Error: {e}")
            continue
def main():
    if len(sys.argv) != 2:
        print("Uso: python run.py <model_name>")
        print("Modelo disponible:")
        print("  qwen2.5-3b  - Qwen2.5-3B-Instruct (3.5GB con 4-bit)")
        print("  (Espacio reservado para modelo grande en el futuro)")
        return
    
    model_name = sys.argv[1].lower()
    
    try:
        tokenizer, model = load_model(model_name)
        if tokenizer is None:
            return
        chat_loop(tokenizer, model, model_name.upper())
    except Exception as e:
        print(f"Error cargando modelo: {e}")
if __name__ == "__main__":
    main()
