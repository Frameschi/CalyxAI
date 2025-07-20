## [1.3.2] - 2025-07-20
### Cambios principales
- El campo "id" ya no aparece en el bloque YAML ni en la tabla de información completa de alimentos.
- "Otras variantes" ahora siempre se muestra como nota separada, fuera del bloque YAML/tabular.
- Visualización estandarizada y robusta para todos los alimentos.

# [1.3.1] - 2025-07-18
### Cambios principales
- Frontend: ahora la información completa de alimentos se muestra en bloque YAML robusto y legible, sin errores de pantalla blanca.
- Se corrigió el import de ConsoleBlockYaml para compatibilidad total con React/Electron.
- El bloque YAML es tolerante a errores y nunca rompe el chat.
- Mejoras de robustez y experiencia visual en la consola de información nutricional.
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
