#!/usr/bin/env python3
"""
Test específico para el problema de "user: 65" al responder sexo
"""

import json
import re

# Cargar fórmulas
with open("data_formulas.json", encoding="utf-8") as f:
    formulas = json.load(f)

def detectar_formula_en_prompt(prompt, formulas):
    prompt_l = prompt.lower()
    
    # CRÍTICO: Detectar el último mensaje del usuario para nueva solicitud
    # Si hay múltiples líneas, tomar la última solicitud como la intención principal
    lineas = prompt.strip().split('\n')
    ultimo_mensaje = ""
    
    # Buscar el último mensaje del usuario (no ai:)
    for linea in reversed(lineas):
        if linea.strip() and not linea.strip().startswith('ai:'):
            ultimo_mensaje = linea.strip().lower()
            if ultimo_mensaje.startswith('user:'):
                ultimo_mensaje = ultimo_mensaje[5:].strip()
            break
    
    print(f"[DEBUG] Último mensaje detectado: '{ultimo_mensaje}'")
    
    # Si hay un mensaje específico reciente, usarlo para detectar la nueva fórmula
    if ultimo_mensaje:
        # PRIMERA PRIORIDAD: Detectar nueva solicitud de composición corporal
        if ("composicion corporal" in ultimo_mensaje or 
            "composición corporal" in ultimo_mensaje or
            "analisis corporal" in ultimo_mensaje or
            "análisis corporal" in ultimo_mensaje):
            print(f"[DEBUG] Nueva solicitud de composición corporal detectada")
            return "composicion_corporal", formulas.get("composicion_corporal")
        
        # SEGUNDA PRIORIDAD: Detectar nueva solicitud de IMC
        solicitudes_imc = [
            "calcular imc", "calcula imc", "imc", "indice de masa corporal", 
            "índice de masa corporal", "calcular mi imc", "calcula mi imc"
        ]
        
        for solicitud in solicitudes_imc:
            if solicitud in ultimo_mensaje:
                print(f"[DEBUG] Nueva solicitud de IMC detectada")
                return "imc", formulas.get("imc")
    
    # FALLBACK: Analizar todo el prompt para detectar fórmula en progreso
    # IMPORTANTE: Priorizar composición corporal si hay múltiples parámetros específicos
    
    # Detectar composición corporal por preguntas específicas en el prompt
    preguntas_composicion = [
        "circunferencia media del brazo", "pliegue cutáneo", "tricipital", 
        "bicipital", "subescapular", "ilíaco", "cmb", "pct", "pcb", "pcse", "pci"
    ]
    
    hay_preguntas_composicion = any(pregunta in prompt_l for pregunta in preguntas_composicion)
    
    if (hay_preguntas_composicion or 
        "composicion corporal" in prompt_l or 
        "composición corporal" in prompt_l):
        print(f"[DEBUG] Composición corporal detectada en progreso")
        return "composicion_corporal", formulas.get("composicion_corporal")
    
    # Detectar IMC por contexto
    if any(solicitud in prompt_l for solicitud in [
        "calcular imc", "calcula imc", "imc", "indice de masa corporal", 
        "índice de masa corporal", "calcular mi imc", "calcula mi imc"
    ]):
        print(f"[DEBUG] IMC detectado en progreso")
        return "imc", formulas.get("imc")
    
    return None, None

# Test del problema específico - prompt exacto del error
print("=== TEST: Problema 'user: 65' al responder sexo ===")
prompt_problema = """user: 65
ai: ¿Cuántos años tienes?
user: 25
ai: ¿Cuál es tu altura en metros? (ejemplo: 1.75)
user: 1.75
ai: ¿Cuál es tu sexo? (M para masculino, F para femenino)
user: M"""

print("Prompt del problema:")
print(prompt_problema)
print("\n" + "="*50)

formula_key, formula = detectar_formula_en_prompt(prompt_problema, formulas)
print(f"Fórmula detectada: {formula_key}")

if formula_key:
    print("✅ ARREGLADO: Detectó fórmula correctamente")
else:
    print("❌ PROBLEMA PERSISTE: No detectó ninguna fórmula")

# Test adicional con contexto más completo
print("\n=== TEST: Con contexto completo de composición corporal ===")
prompt_completo = """user: composicion corporal
ai: ¿Cuál es tu peso en kg?
user: 65
ai: ¿Cuántos años tienes?
user: 25
ai: ¿Cuál es tu altura en metros? (ejemplo: 1.75)
user: 1.75
ai: ¿Cuál es tu sexo? (M para masculino, F para femenino)
user: M"""

formula_key2, formula2 = detectar_formula_en_prompt(prompt_completo, formulas)
print(f"Fórmula detectada: {formula_key2}")

if formula_key2 == "composicion_corporal":
    print("✅ CORRECTO: Detectó composición corporal")
else:
    print("❌ ERROR: No detectó composición corporal")
