# utils/validators.py
# Módulo para validaciones reutilizables en el backend de CalyxAI

def validate_food_input(food_data):
    """
    Valida la entrada de datos de alimentos.
    Args:
        food_data (dict): Datos del alimento.
    Returns:
        bool, str: True y mensaje vacío si es válido, False y mensaje de error si no.
    """
    required_fields = ["nombre", "cantidad", "unidad"]
    for field in required_fields:
        if field not in food_data:
            return False, f"Falta el campo requerido: {field}"
        if not food_data[field]:
            return False, f"El campo '{field}' no puede estar vacío."
    # Validación de cantidad
    try:
        cantidad = float(food_data["cantidad"])
        if cantidad <= 0:
            return False, "La cantidad debe ser mayor a cero."
    except ValueError:
        return False, "La cantidad debe ser un número."
    return True, ""
