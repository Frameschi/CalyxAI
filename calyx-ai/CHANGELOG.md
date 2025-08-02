# Changelog

## [1.3.4] - 2025-08-02
### Nuevas características principales
- **Sistema de cálculo automático de fórmulas**: Implementación completa del sistema de IMC y otras fórmulas nutricionales
- **Consola técnica animada**: Nuevo componente `ConsoleBlock` que muestra los cálculos paso a paso con animación terminal profesional
- **Animación terminal mejorada**: Cursor único parpadeante (█) con efecto typewriter de 50ms por carácter
- **Conversión automática de unidades**: Sistema robusto que convierte automáticamente:
  - Altura: 175cm → 1.75m, centímetros → metros
  - Peso: 80000g → 80kg, gramos → kilogramos
- **Detección inteligente de parámetros**: Regex avanzados que detectan múltiples formatos:
  - "175cm", "1.75m", "peso: 80kg", "80 kg peso"
  - Manejo de comas como separador decimal
  - Tolerancia a espacios y variaciones de escritura

### Mejoras técnicas
- **TerminalTypewriter component**: Animación de terminal personalizada sin dependencias externas
- **Regex patterns mejorados**: Patrones más robustos para detección de unidades y valores
- **Validación de entrada**: Mejor manejo de errores en conversiones numéricas
- **Filtrado de mensajes vacíos**: Eliminación de mensajes duplicados en el chat
- **Optimización de animaciones**: Timing preciso para experiencia fluida

### Correcciones
- Solucionado: Múltiples cursores en animación terminal
- Solucionado: Conversión incorrecta de 175cm mostrando 175.0m en lugar de 1.75m
- Solucionado: Mensajes vacíos apareciendo en el chat
- Solucionado: Animación prematura antes de completar cálculos

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
