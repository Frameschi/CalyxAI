#!/usr/bin/env python3
"""
Test para verificar que las solicitudes de diferentes fórmulas se separen correctamente
"""

# Simular prompt de conversación donde primero se calculó IMC y luego se pide composición corporal
prompt_test = """user: IMC
ai: ¿Cuál es tu peso en kg?
user: 65
ai: ¿Cuál es tu altura en metros? (ejemplo: 1.75)
user: 1.75
ai: 🧮Cálculo
> Cálculo del IMC

DATOS DE ENTRADA:
Peso: 65.0 kg
Altura: 1.75 m

FÓRMULA:
IMC = peso / altura²

SUSTITUCIÓN:
IMC = 65.0 / (1.75)^2

RESULTADO:
IMC = 21.22 (Peso normal)
user: composicion corporal"""

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
    
    return None, None

def extraer_parametros_usuario(prompt, formula, es_nueva_solicitud=False):
    params = {}
    texto = prompt.lower()
    
    # CRÍTICO: Si es una nueva solicitud de fórmula, solo buscar parámetros 
    # en el contexto reciente, no en toda la conversación histórica
    if es_nueva_solicitud:
        print(f"[DEBUG] Nueva solicitud detectada - limitando búsqueda a contexto reciente")
        # Solo buscar en las últimas 3 líneas de la conversación
        lineas = prompt.strip().split('\n')
        contexto_reciente = lineas[-3:] if len(lineas) > 3 else lineas
        texto = '\n'.join(contexto_reciente).lower()
        print(f"[DEBUG] Contexto reciente: {texto}")
    else:
        # Buscar en TODA la conversación para recolección progresiva de parámetros
        print(f"[DEBUG] Recolección progresiva - analizando toda la conversación")
    
    # Buscar peso y altura en el texto
    patrones_peso = [
        r'(\d{1,3}(?:[\.,]\d+)?)\s*(?:kg|kilogramos?|kilos?)',
        r'peso.*?(\d{1,3}(?:[\.,]\d+)?)',
        r'¿cuál es tu peso.*?(\d{1,3}(?:[\.,]\d+)?)'
    ]
    
    for patron in patrones_peso:
        matches = re.findall(patron, texto, re.IGNORECASE | re.DOTALL)
        for match in matches:
            valor = float(match.replace(",", "."))
            if 30 <= valor <= 200:
                params["peso"] = str(valor)
                print(f"[DEBUG] Peso encontrado: {valor}")
                break
        if "peso" in params:
            break
    
    patrones_altura = [
        r'(\d{1,2}[\.,]\d{1,2})\s*(?:m|metros?)',
        r'altura.*?(\d{1,2}[\.,]\d{1,2})'
    ]
    
    for patron in patrones_altura:
        matches = re.findall(patron, texto, re.IGNORECASE | re.DOTALL)
        for match in matches:
            valor = float(match.replace(",", "."))
            if 1.0 <= valor <= 2.5:
                params["altura"] = str(valor)
                print(f"[DEBUG] Altura encontrada: {valor}")
                break
        if "altura" in params:
            break
    
    return params

# Test
print("=== TEST: Separación de Fórmulas ===")
print("Prompt completo:")
print(prompt_test)
print("\n" + "="*50)

formula_key, formula = detectar_formula_en_prompt(prompt_test, formulas)
print(f"\nFórmula detectada: {formula_key}")

if formula:
    # Detectar si es nueva solicitud
    lineas = prompt_test.strip().split('\n')
    ultimo_mensaje = ""
    
    for linea in reversed(lineas):
        if linea.strip() and not linea.strip().startswith('ai:'):
            ultimo_mensaje = linea.strip().lower()
            if ultimo_mensaje.startswith('user:'):
                ultimo_mensaje = ultimo_mensaje[5:].strip()
            break
    
    es_nueva_solicitud = False
    if ultimo_mensaje:
        nuevas_solicitudes = [
            "composicion corporal", "composición corporal", "analisis corporal", 
            "análisis corporal", "calcular imc", "calcula imc", "imc"
        ]
        for solicitud in nuevas_solicitudes:
            if solicitud in ultimo_mensaje:
                es_nueva_solicitud = True
                break
    
    print(f"Es nueva solicitud: {es_nueva_solicitud}")
    
    params = extraer_parametros_usuario(prompt_test, formula, es_nueva_solicitud)
    print(f"Parámetros extraídos: {params}")
    
    # Verificar parámetros faltantes
    faltantes = []
    for param in formula["parametros"]:
        if param["nombre"] not in params:
            faltantes.append(param["nombre"])
    
    print(f"Parámetros faltantes: {faltantes}")
    
    # RESULTADO ESPERADO:
    # - Debe detectar "composicion_corporal" como fórmula
    # - NO debe encontrar peso ni altura en contexto reciente (es nueva solicitud)
    # - Debe faltar TODOS los parámetros de composición corporal
    
    print("\n=== EVALUACIÓN ===")
    if formula_key == "composicion_corporal":
        print("✅ Correctamente detectó composición corporal")
    else:
        print("❌ ERROR: No detectó composición corporal")
    
    if es_nueva_solicitud and len(params) == 0:
        print("✅ Correctamente NO reutilizó parámetros del IMC anterior")
    else:
        print("❌ ERROR: Reutilizó parámetros del IMC anterior")
    
    if len(faltantes) == len(formula["parametros"]):
        print("✅ Correctamente identificó que faltan TODOS los parámetros")
    else:
        print("❌ ERROR: No identificó que faltan todos los parámetros")

else:
    print("❌ ERROR: No se detectó ninguna fórmula")
