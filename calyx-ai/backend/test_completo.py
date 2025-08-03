#!/usr/bin/env python3
"""
Test completo para verificar separación de fórmulas Y recolección progresiva
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
    if ("composicion corporal" in prompt_l or 
        "composición corporal" in prompt_l or
        "análisis corporal" in prompt_l or
        ("circunferencia media del brazo" in prompt_l and "pliegue cutáneo" in prompt_l)):
        return "composicion_corporal", formulas.get("composicion_corporal")
    
    # Buscar IMC en todo el prompt
    solicitudes_imc = [
        "calcular imc", "calcula imc", "imc", "indice de masa corporal", 
        "índice de masa corporal", "calcular mi imc", "calcula mi imc"
    ]
    
    for solicitud in solicitudes_imc:
        if solicitud in prompt_l:
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
    
    # Fallback para números sueltos cerca de preguntas de peso
    if "peso" not in params:
        lineas = texto.split('\n')
        for i, linea in enumerate(lineas):
            if "peso" in linea and i + 1 < len(lineas):
                siguiente = lineas[i + 1].strip()
                numeros = re.findall(r'(\d{1,3}(?:[\.,]\d+)?)', siguiente)
                for num in numeros:
                    valor = float(num.replace(",", "."))
                    if 30 <= valor <= 200:
                        params["peso"] = str(valor)
                        print(f"[DEBUG] Peso encontrado (fallback): {valor}")
                        break
                if "peso" in params:
                    break
    
    # Buscar altura
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
    
    # Fallback para altura
    if "altura" not in params:
        lineas = texto.split('\n')
        for i, linea in enumerate(lineas):
            if "altura" in linea and i + 1 < len(lineas):
                siguiente = lineas[i + 1].strip()
                numeros = re.findall(r'(\d{1,3}(?:[\.,]\d+)?)', siguiente)
                for num in numeros:
                    valor = float(num.replace(",", "."))
                    if 1.0 <= valor <= 2.5:
                        params["altura"] = str(valor)
                        print(f"[DEBUG] Altura encontrada (fallback): {valor}")
                        break
                    elif 140 <= valor <= 220:
                        params["altura"] = str(valor / 100)
                        print(f"[DEBUG] Altura encontrada en cm (fallback): {valor} -> {valor/100}m")
                        break
                if "altura" in params:
                    break
    
    # Buscar edad
    if "edad" not in params:
        lineas = texto.split('\n')
        for i, linea in enumerate(lineas):
            if "años" in linea and i + 1 < len(lineas):
                siguiente = lineas[i + 1].strip()
                numeros = re.findall(r'(\d{1,3})', siguiente)
                for num in numeros:
                    valor = int(num)
                    if 10 <= valor <= 120:
                        params["edad"] = str(valor)
                        print(f"[DEBUG] Edad encontrada (fallback): {valor}")
                        break
                if "edad" in params:
                    break
    
    # Buscar sexo
    if "sexo" not in params:
        lineas = texto.split('\n')
        for i, linea in enumerate(lineas):
            if "sexo" in linea and i + 1 < len(lineas):
                siguiente = lineas[i + 1].strip()
                match = re.search(r'\b([MFmf])\b', siguiente)
                if match:
                    params["sexo"] = match.group(1).upper()
                    print(f"[DEBUG] Sexo encontrado (fallback): {match.group(1).upper()}")
                    break
    
    return params

# Test 1: Cambio de fórmula (debe ser nueva solicitud)
print("=== TEST 1: Cambio de Fórmula (IMC -> Composición Corporal) ===")
prompt1 = """user: IMC
ai: ¿Cuál es tu peso en kg?
user: 65
ai: ¿Cuál es tu altura en metros? (ejemplo: 1.75)
user: 1.75
ai: IMC = 21.22 (Peso normal)
user: composicion corporal"""

formula_key, formula = detectar_formula_en_prompt(prompt1, formulas)
es_nueva_solicitud = False
if formula_key:
    lineas = prompt1.strip().split('\n')
    ultimo_mensaje = ""
    
    for linea in reversed(lineas):
        if linea.strip() and not linea.strip().startswith('ai:'):
            ultimo_mensaje = linea.strip().lower()
            if ultimo_mensaje.startswith('user:'):
                ultimo_mensaje = ultimo_mensaje[5:].strip()
            break
    
    if ultimo_mensaje:
        es_respuesta_numero = re.match(r'^\s*\d+(\.\d+)?\s*$', ultimo_mensaje.strip())
        es_respuesta_sexo = re.match(r'^\s*[mf]\s*$', ultimo_mensaje.strip(), re.IGNORECASE)
        es_respuesta_simple = es_respuesta_numero or es_respuesta_sexo
        
        if not es_respuesta_simple:
            nuevas_solicitudes = [
                "composicion corporal", "composición corporal", "analisis corporal", 
                "análisis corporal", "calcular imc", "calcula imc", "imc"
            ]
            for solicitud in nuevas_solicitudes:
                if solicitud in ultimo_mensaje:
                    es_nueva_solicitud = True
                    break

params = extraer_parametros_usuario(prompt1, formula, es_nueva_solicitud)
print(f"Fórmula: {formula_key}, Nueva solicitud: {es_nueva_solicitud}, Params: {params}")
print("✅ CORRECTO: No debe reutilizar peso/altura del IMC" if len(params) == 0 else "❌ ERROR: Reutilizó parámetros")

# Test 2: Recolección progresiva dentro de la misma fórmula
print("\n=== TEST 2: Recolección Progresiva (Respuestas a Composición Corporal) ===")
prompt2 = """user: composicion corporal
ai: ¿Cuál es tu peso en kg?
user: 65
ai: ¿Cuántos años tienes?
user: 25"""

formula_key2, formula2 = detectar_formula_en_prompt(prompt2, formulas)
es_nueva_solicitud2 = False
if formula_key2:
    lineas = prompt2.strip().split('\n')
    ultimo_mensaje = ""
    
    for linea in reversed(lineas):
        if linea.strip() and not linea.strip().startswith('ai:'):
            ultimo_mensaje = linea.strip().lower()
            if ultimo_mensaje.startswith('user:'):
                ultimo_mensaje = ultimo_mensaje[5:].strip()
            break
    
    if ultimo_mensaje:
        es_respuesta_numero = re.match(r'^\s*\d+(\.\d+)?\s*$', ultimo_mensaje.strip())
        es_respuesta_sexo = re.match(r'^\s*[mf]\s*$', ultimo_mensaje.strip(), re.IGNORECASE)
        es_respuesta_simple = es_respuesta_numero or es_respuesta_sexo
        
        if not es_respuesta_simple:
            nuevas_solicitudes = [
                "composicion corporal", "composición corporal", "analisis corporal", 
                "análisis corporal", "calcular imc", "calcula imc", "imc"
            ]
            for solicitud in nuevas_solicitudes:
                if solicitud in ultimo_mensaje:
                    es_nueva_solicitud2 = True
                    break

params2 = extraer_parametros_usuario(prompt2, formula2, es_nueva_solicitud2)
print(f"Fórmula: {formula_key2}, Nueva solicitud: {es_nueva_solicitud2}, Params: {params2}")
print("✅ CORRECTO: Debe acumular peso y edad" if "peso" in params2 and "edad" in params2 else "❌ ERROR: No acumuló parámetros")
