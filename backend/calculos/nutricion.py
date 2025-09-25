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


# ========== FUNCIONES AVANZADAS PARA HERRAMIENTAS DE IA ==========

def buscar_alimentos_filtrados(criterios: Dict[str, Any], limite: int = 10) -> List[Dict[str, Any]]:
    """
    Busca alimentos aplicando filtros avanzados.

    Args:
        criterios: Diccionario con criterios de filtro. Ejemplos:
            {
                "sodio_max": 100,      # sodio < 100mg
                "fibra_min": 5,        # fibra > 5g
                "calorias_max": 200,   # energia < 200kcal
                "proteina_min": 10,    # proteina > 10g
                "lipidos_max": 5,      # lipidos < 5g
                "grupo": "verduras",   # grupo específico
                "nombre_like": "arroz" # búsqueda por nombre
            }
        limite: Máximo número de resultados

    Returns:
        Lista de alimentos que cumplen los criterios
    """
    try:
        import sqlite3
        import os
        import unicodedata

        db_path = os.path.join(os.path.dirname(__file__), "..", "datainfo.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Función para quitar acentos
        def quitar_acentos(texto):
            return ''.join(c for c in unicodedata.normalize('NFD', texto)
                          if unicodedata.category(c) != 'Mn')

        # Construir consulta SQL dinámica
        where_conditions = []
        params = []

        # Filtros numéricos
        filtros_numericos = {
            "sodio_max": ("sodio (mg)", "<"),
            "fibra_min": ("fibra (g)", ">"),
            "calorias_max": ("energia (kcal)", "<"),
            "proteina_min": ("proteina (g)", ">"),
            "lipidos_max": ("lipidos (g)", "<"),
            "calcio_min": ("calcio (mg)", ">"),
            "hierro_min": ("hierro (mg)", ">"),
            "potasio_min": ("potasio (mg)", ">")
        }

        for criterio, (columna, operador) in filtros_numericos.items():
            if criterio in criterios and criterios[criterio] is not None:
                where_conditions.append(f"`{columna}` {operador} ?")
                params.append(criterios[criterio])

        # Filtro por grupo
        if "grupo" in criterios and criterios["grupo"]:
            grupo_sin_acentos = quitar_acentos(criterios["grupo"].lower())
            where_conditions.append("LOWER(`grupo de alimentos`) LIKE ?")
            params.append(f"%{grupo_sin_acentos}%")

        # Filtro por nombre
        if "nombre_like" in criterios and criterios["nombre_like"]:
            nombre_sin_acentos = quitar_acentos(criterios["nombre_like"].lower())
            where_conditions.append("LOWER(alimento) LIKE ?")
            params.append(f"%{nombre_sin_acentos}%")

        # Construir consulta final
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        query = f"""
        SELECT * FROM alimentos
        WHERE {where_clause}
        ORDER BY `energia (kcal)` ASC
        LIMIT ?
        """
        params.append(limite)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]

        # Convertir a lista de diccionarios
        resultados = []
        for row in rows:
            alimento_dict = dict(zip(columns, row))
            resultados.append({
                "id": alimento_dict.get("id"),
                "alimento": alimento_dict.get("alimento"),
                "grupo": alimento_dict.get("grupo de alimentos"),
                "cantidad_base": f"{alimento_dict.get('cantidad', 100)} {alimento_dict.get('unidad', 'g')}",
                "nutrientes": {
                    "energia_kcal": alimento_dict.get("energia (kcal)"),
                    "proteina_g": alimento_dict.get("proteina (g)"),
                    "lipidos_g": alimento_dict.get("lipidos (g)"),
                    "hidratos_carbono_g": alimento_dict.get("hidratos de carbono (g)"),
                    "fibra_g": alimento_dict.get("fibra (g)"),
                    "azucar_g": alimento_dict.get("azucar (g)"),
                    "sodio_mg": alimento_dict.get("sodio (mg)"),
                    "calcio_mg": alimento_dict.get("calcio (mg)"),
                    "hierro_mg": alimento_dict.get("hierro (mg)"),
                    "potasio_mg": alimento_dict.get("potasio (mg)")
                }
            })

        conn.close()
        return resultados

    except Exception as e:
        print(f"[ERROR] Error en buscar_alimentos_filtrados: {e}")
        return []


def calcular_composicion_total(alimentos: List[str], porciones: List[float] = None) -> Dict[str, Any]:
    """
    Calcula la composición nutricional total de una lista de alimentos.

    Args:
        alimentos: Lista de nombres de alimentos
        porciones: Lista de factores de porción (1.0 = porción base, 2.0 = doble porción, etc.)
                   Si no se especifica, usa 1.0 para todos

    Returns:
        Diccionario con composición total y desglose por alimento
    """
    try:
        import os
        import sqlite3

        if not alimentos:
            return {"error": "Lista de alimentos vacía"}

        if porciones is None:
            porciones = [1.0] * len(alimentos)
        elif len(porciones) != len(alimentos):
            return {"error": "Número de porciones no coincide con número de alimentos"}

        db_path = os.path.join(os.path.dirname(__file__), "..", "datainfo.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        composicion_total = {
            "energia_kcal": 0.0,
            "proteina_g": 0.0,
            "lipidos_g": 0.0,
            "hidratos_carbono_g": 0.0,
            "fibra_g": 0.0,
            "azucar_g": 0.0,
            "sodio_mg": 0.0,
            "calcio_mg": 0.0,
            "hierro_mg": 0.0,
            "potasio_mg": 0.0
        }

        desglose = []

        for i, alimento in enumerate(alimentos):
            # Buscar alimento
            cursor.execute("SELECT * FROM alimentos WHERE LOWER(alimento) LIKE ? LIMIT 1",
                          (f"%{alimento.lower()}%",))
            row = cursor.fetchone()

            if row:
                columns = [description[0] for description in cursor.description]
                alimento_dict = dict(zip(columns, row))
                factor = porciones[i]

                # Sumar a composición total
                for nutriente, total in composicion_total.items():
                    columna_db = {
                        "energia_kcal": "energia (kcal)",
                        "proteina_g": "proteina (g)",
                        "lipidos_g": "lipidos (g)",
                        "hidratos_carbono_g": "hidratos de carbono (g)",
                        "fibra_g": "fibra (g)",
                        "azucar_g": "azucar (g)",
                        "sodio_mg": "sodio (mg)",
                        "calcio_mg": "calcio (mg)",
                        "hierro_mg": "hierro (mg)",
                        "potasio_mg": "potasio (mg)"
                    }.get(nutriente)

                    if columna_db:
                        valor = alimento_dict.get(columna_db, 0)
                        try:
                            valor_num = float(valor) if valor else 0.0
                            composicion_total[nutriente] += valor_num * factor
                        except (ValueError, TypeError):
                            pass

                # Agregar al desglose
                desglose.append({
                    "alimento": alimento_dict.get("alimento"),
                    "porcion": f"{factor}x {alimento_dict.get('cantidad', 100)} {alimento_dict.get('unidad', 'g')}",
                    "energia_kcal": (float(alimento_dict.get("energia (kcal)", 0) or 0)) * factor
                })

        conn.close()

        return {
            "composicion_total": composicion_total,
            "desglose_por_alimento": desglose,
            "numero_alimentos": len(alimentos),
            "total_alimentos_encontrados": len([d for d in desglose if d["energia_kcal"] > 0])
        }

    except Exception as e:
        print(f"[ERROR] Error en calcular_composicion_total: {e}")
        return {"error": str(e)}


def generar_recomendaciones_dieta(restricciones: Dict[str, Any], objetivo_calorico: int = 2000) -> Dict[str, Any]:
    """
    Genera recomendaciones básicas de dieta basadas en restricciones.

    Args:
        restricciones: Diccionario con restricciones. Ejemplos:
            {
                "vegetariano": True,
                "vegano": False,
                "bajo_sodio": True,
                "alto_fibra": False,
                "diabetico": False
            }
        objetivo_calorico: Calorías objetivo diario

    Returns:
        Recomendaciones de dieta con alimentos sugeridos
    """
    try:
        recomendaciones = {
            "objetivo_calorico_diario": objetivo_calorico,
            "distribucion_recomendada": {
                "desayuno": "25-30%",
                "almuerzo": "30-35%",
                "cena": "25-30%",
                "snacks": "10-15%"
            },
            "grupos_alimentarios": {},
            "restricciones_aplicadas": restricciones,
            "sugerencias_alimentos": []
        }

        # Lógica básica de recomendaciones según restricciones
        if restricciones.get("bajo_sodio"):
            recomendaciones["sugerencias_alimentos"].extend([
                "frutas frescas (manzana, pera, naranja)",
                "verduras frescas (lechuga, tomate, pepino)",
                "cereales integrales sin sal",
                "productos lácteos bajos en sodio"
            ])

        if restricciones.get("alto_fibra"):
            recomendaciones["sugerencias_alimentos"].extend([
                "legumbres (lentejas, garbanzos, frijoles)",
                "frutas con cáscara (manzana, pera)",
                "verduras de hoja verde",
                "cereales integrales (avena, quinoa, arroz integral)"
            ])

        if restricciones.get("vegetariano"):
            recomendaciones["grupos_alimentarios"]["proteinas"] = [
                "legumbres", "huevos", "lácteos", "frutos secos", "tofu", "quinoa"
            ]

        if restricciones.get("vegano"):
            recomendaciones["grupos_alimentarios"]["proteinas"] = [
                "legumbres", "frutos secos", "semillas", "tofu", "tempeh", "seitán"
            ]

        if restricciones.get("diabetico"):
            recomendaciones["sugerencias_alimentos"].extend([
                "verduras de hoja verde",
                "pescado azul",
                "frutos secos en moderación",
                "productos integrales de bajo índice glucémico"
            ])

        # Si no hay restricciones específicas, recomendaciones generales
        if not any(restricciones.values()):
            recomendaciones["sugerencias_alimentos"].extend([
                "variedad de frutas y verduras",
                "proteínas magras (pescado, pollo, legumbres)",
                "cereales integrales",
                "lácteos bajos en grasa",
                "grasas saludables (aguacate, nueces, aceite de oliva)"
            ])

        return recomendaciones

    except Exception as e:
        print(f"[ERROR] Error en generar_recomendaciones_dieta: {e}")
        return {"error": str(e)}
