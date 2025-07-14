# Changelog

## [1.2.2] - 2025-07-14
### Cambios principales
- Prompt del sistema actualizado: ahora usa delimitadores <|system|>, <|user|>, <|assistant|> y reglas claras para modular el comportamiento entre nutrición y asistente general.
- Respuestas de la IA mucho más coherentes, breves y profesionales, sin historias inventadas ni desvíos de rol.
- Cálculo automático proporcional de calorías y nutrientes según la cantidad solicitada por el usuario.
- Límite de variantes de alimentos sugeridos (máx. 4).
- requirements.txt actualizado con todas las dependencias necesarias (FastAPI, Uvicorn, Transformers, Torch, BitsAndBytes).
- Mejoras en el filtrado post-procesado de respuestas para evitar temas irrelevantes.
- Eliminación de archivos temporales y limpieza general.
