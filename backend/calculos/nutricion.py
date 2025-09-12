# calculos/nutricion.py
# Lógica de cálculo y formateo de información nutricional para CalyxAI

from typing import Dict, Any, List

def calcular_info_nutricional_basica(food_data: Dict[str, Any], info_nutricional: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Devuelve la información nutricional básica en formato de filas (clave, valor).
    """
    filas = []
    for key, value in info_nutricional.items():
        filas.append({"clave": key, "valor": str(value)})
    return filas

def calcular_info_nutricional_completa(food_data: Dict[str, Any], info_nutricional: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Devuelve la información nutricional completa, desglosada para animación en consola.
    """
    desglosado = []
    for key, value in info_nutricional.items():
        desglosado.append({"linea": f"{key}: {value}"})
    return desglosado

def calcular_desglose_calculos(food_data: Dict[str, Any], pasos: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Devuelve el desglose paso a paso de los cálculos para animación en consola.
    """
    animacion = []
    for paso in pasos:
        animacion.append({"linea": paso["descripcion"]})
    return animacion
