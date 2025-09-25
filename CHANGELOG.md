# Changelog

## [1.7.2] - 2025-09-25
### 🧠 CARACTERÍSTICA MAYOR: Sistema Híbrido de IA con Prompts Especializados
- **Sistema de 3 prompts inteligentes**: Implementación completa de separación de responsabilidades
  - **Prompt Conversacional**: Maneja interacciones sociales y consultas generales (sin herramientas)
  - **Prompt Nutricional**: Activa herramientas de base de datos para consultas sobre alimentos
  - **Prompt Médico**: Formatea cálculos automáticos en console blocks estructurados
- **Detección automática de consultas**: Sistema inteligente que identifica el tipo de consulta y aplica el prompt apropiado
- **Separación perfecta de funcionalidades**: Conversaciones, nutrición y cálculos médicos completamente independientes

### 🐛 CORRECCIÓN CRÍTICA: Bug de Parámetros Reutilizados en Cálculos Médicos
- **Problema identificado**: Cálculos médicos reutilizaban parámetros de consultas anteriores
- **Causa raíz**: Prompt `build_calculation_prompt` contenía valores hardcodeados en ejemplos
- **Solución implementada**: Remoción de valores hardcodeados y uso exclusivo de datos reales del JSON
- **Validación completa**: Cada cálculo ahora usa únicamente los parámetros de la consulta actual

### 🗣️ OPTIMIZACIÓN: Limpieza del Prompt Conversacional
- **Eliminación de referencias cruzadas**: Removida mención a TOOL_CALL del prompt conversacional
- **Separación limpia**: Prompt conversacional enfocado únicamente en personalidad y tono
- **Prevención de confusiones**: IA no intenta usar herramientas en conversaciones normales

### 🔧 Mejoras técnicas y estabilidad
- **Arquitectura modular**: Sistema de prompts completamente desacoplado y mantenible
- **Validación de integridad**: Verificación de que cada prompt maneja solo su responsabilidad
- **Optimización de rendimiento**: Reducción de llamadas innecesarias entre componentes

## [1.7.1] - 2025-09-20
### 🚀 CARACTERÍSTICA MAYOR: Migración Completa a Qwen2.5-3B con Transformers
- **Migración total de Ollama**: Eliminación completa de DeepSeek-R1 y sistema Ollama
- **Qwen2.5-3B exclusivo**: Implementación de Qwen/Qwen2.5-3B-Instruct con cuantización 4-bit
- **Transformers + Accelerate**: Sistema de inferencia optimizado con GPU para GTX 1050 Ti
- **Eliminación de dependencias**: Removidos todos los paquetes y configuraciones de Ollama
- **Limpieza completa**: Eliminadas todas las referencias a modelos antiguos (DeepSeek-R1, Phi-3, etc.)

### 🧮 MEJORA CRÍTICA: Formateo de Cálculos Médicos
- **Formato estructurado IMC**: Implementación de formato profesional con secciones claras (DATOS DE ENTRADA, FÓRMULA, SUSTITUCIÓN, OPERACIÓN, RESULTADO)
- **Prompt universal inteligente**: Sistema de formateo que funciona para todas las fórmulas médicas manteniendo consistencia
- **Eliminación de duplicaciones**: Corrección de secciones duplicadas en la presentación de cálculos
- **Títulos correctos**: Ajuste de nomenclatura ("Cálculo de IMC" en lugar de "Cálculo del IMC")

### 🗣️ OPTIMIZACIÓN: Sistema de Conversación Mejorado
- **Respuestas contextuales**: Corrección de IA que mencionaba cálculos anteriores en respuestas de agradecimiento
- **Historial inteligente**: Sistema que ignora solicitudes antiguas y responde únicamente al último mensaje
- **Separación de contextos**: Diferenciación clara entre conversaciones normales y peticiones de cálculo
- **Experiencia natural**: Respuestas breves y apropiadas para interacciones sociales

### 🔧 Mejoras técnicas y estabilidad
- **Extracción de parámetros**: Corrección para usar solo el último mensaje del usuario en cálculos
- **Gestión de memoria GPU**: Optimización de 4GB VRAM para Qwen2.5-3B
- **Sistema de tokens dinámico**: Asignación inteligente de tokens según complejidad
- **Code cleanup**: Eliminación de código legacy y referencias obsoletas

## [1.7.0] - 2025-09-19
### 🧠 CARACTERÍSTICA MAYOR: Sistema de Prompts Optimizado y Separado
- **Separación clara de contextos**: Sistema de prompts completamente separado entre conversaciones normales y cálculos médicos
- **Prompt universal**: Implementación de instrucciones universales de formateo para todos los cálculos médicos
- **Eliminación de código redundante**: Removida función `generate_for_calculations` y prompts simplificados innecesarios
- **Optimización de tokens**: Sistema dinámico de asignación de tokens basado en complejidad de fórmulas (800-1500 tokens)
- **Limpieza completa del código**: Eliminados residuos de prompts antiguos y lógica duplicada

### ⚡ OPTIMIZACIÓN: Arquitectura de IA Mejorada
- **Sistema de detección inteligente**: 13 fórmulas médicas detectadas automáticamente con patrones expandidos
- **Conversaciones naturales**: Respuestas breves y contextuales para interacciones normales
- **Cálculos formateados**: Presentación estructurada en console blocks para resultados médicos
- **Separación de responsabilidades**: Backend maneja cálculos, frontend presenta resultados
- **Actualización de versiones**: VERSION.txt, package.json, Settings.tsx y archivos de distribución actualizados a 1.7.0

### 🔧 Mejoras técnicas y estabilidad
- **Validación sintáctica**: Verificación completa de archivos Python después de cambios
- **Gestión de memoria**: Optimización de recursos para cálculos complejos
- **Error handling**: Mejor manejo de errores en detección y procesamiento de fórmulas
- **Code cleanup**: Eliminación de funciones obsoletas y referencias antiguas

## [1.6.5] - 2025-09-17
### 🧹 CARACTERÍSTICA MAYOR: Sistema Exclusivo DeepSeek-R1 Sin Fallbacks
- **Eliminación total de fallbacks**: Removidos todos los métodos de respuesta hardcoded y servidor de respaldo
- **DeepSeek-R1 exclusivo**: Sistema configurado únicamente para usar DeepSeek-R1 via Ollama
- **Parsing inteligente de thinking**: Separación automática entre proceso de razonamiento y respuesta final
- **Timeout extendido**: Aumentado a 5 minutos para permitir razonamiento profundo de DeepSeek-R1
- **Limpieza completa**: Eliminados todos los métodos HuggingFace, Phi-3 y lógica de fallback
- **Actualización de versiones**: VERSION.txt, package.json y Settings.tsx actualizados a 1.6.5

## [1.6.4] - 2025-09-10
### 📦 Respaldo integral y sincronización total
- **Se sube TODO el proyecto**: backend, frontend, scripts, documentación, changelogs y archivos de configuración.
- **Garantía de integridad**: respaldo completo para futuras versiones y distribución.
- **Actualización de VERSION.txt a 1.6.4.**
- Preparado para desarrollo y despliegue profesional.

## [1.6.1] - 2025-09-09
### 🧠 CARACTERÍSTICA MAYOR: DeepSeek-R1 "Thinking" Dropdown
- **ChatGPT-style Thinking**: Implementado dropdown colapsible para mostrar el proceso de razonamiento de DeepSeek-R1
- **Separación inteligente**: Separación automática entre `<think>` y respuesta final
- **UI elegante**: Dropdown con ícono de cerebro 🧠 y animación suave
- **Experiencia mejorada**: Los usuarios pueden ver el proceso de pensamiento detallado del modelo

### ⚡ OPTIMIZACIÓN CRÍTICA: GPU Performance Boost
- **GPU utilization**: Incremento dramático de 1% → 42% utilización GPU
- **Memory optimization**: VRAM usage optimizado de 612MB → 3.7GB (93% GTX 1050 Ti)
- **Configuración GPU**: Variables de entorno optimizadas para máximo rendimiento
  - `OLLAMA_NUM_GPU_LAYERS=32`
  - `OLLAMA_GPU_FRACTION=0.8`
- **CPU/GPU Balance**: Distribución optimizada 42%/58% CPU/GPU para hardware limitado

### 🔧 Fixes técnicos y estabilidad
- **Ollama integration**: Conexión mejorada entre backend y Ollama
- **Model loading**: Precarga automática de DeepSeek-R1 para mejor responsividad
- **Error handling**: Manejo mejorado de timeouts y conexiones
- **Code cleanup**: Eliminación de archivos temporales y de testing

## [1.6.0] - 2025-09-06
### 🤖 NUEVO MODELO: DeepSeek-R1 - Razonamiento matemático avanzado
- **Dual-model system**: Agregado DeepSeek-R1-0528-Qwen3-8B-GGUF junto a Phi-3-Mini
- **Modelo especializado**: DeepSeek-R1 optimizado para razonamiento matemático y cálculos médicos
- **Switching dinámico**: Cambio fluido entre modelos según necesidades del usuario
- **GGUF optimizado**: Implementación eficiente con Ollama para mejor rendimiento

### 🚀 Optimización MAYOR de rendimiento
- **Polling fix**: Eliminado polling excesivo del backend (reducido de múltiples timers overlap)
- **Procesos optimizados**: Fix de 4 procesos Python duplicados ejecutándose simultáneamente
- **ModelStatusContext**: Sistema centralizado de gestión de estado con intervalos controlados
- **Memoria optimizada**: Reducción significativa del uso de recursos del sistema

### 🎨 Mejoras de interfaz y experiencia
- **Loading animado**: Ícono de loading rotando durante "Cambiando modelo..."
- **Logo integration**: Reemplazado emoji ADN con logo profesional en chat
- **UI más limpia**: Eliminadas líneas separadoras innecesarias
- **Información dinámica**: Settings ahora muestra info del modelo actualmente activo
- **Mensajes contextuales**: Eliminados textos hardcoded, todo dinámico según modelo activo

### 🧹 Limpieza masiva del proyecto
- **Archivos obsoletos**: Eliminados scripts de debug, tests antiguos y archivos duplicados
- **Estructura optimizada**: Proyecto reorganizado y limpio para mejor mantenimiento
- **Código legacy**: Removidos componentes y hooks no utilizados
- **Gitignore actualizado**: Mejor gestión de archivos temporales y builds

### 🔧 Mejoras técnicas
- **Error handling**: Mejor manejo de errores durante cambio de modelos
- **Estado centralizado**: Gestión unificada del estado de modelos en toda la app
- **Performance monitoring**: Mejor tracking de procesos backend
- **Code quality**: Refactoring general para mejor legibilidad y mantenimiento

## [1.5.5] - 2025-08-29
### 🧠 Optimización MAYOR del motor de IA Phi-3
- **Formula detection mejorada**: Detección más precisa limitada a las últimas 3 líneas (vs 10 anteriormente)
- **Filtrado de parámetros**: Eliminación de contaminación entre cálculos sucesivos
- **Respuestas consistentes**: Fix de respuestas "¡Hola!" incorrectas durante cálculos en progreso
- **Detección de números**: Corrección en el parsing de inputs numéricos (altura, peso, etc.)
- **Console blocks exclusivos**: Todos los resultados de cálculos van exclusivamente al console block
- **Flujo IMC optimizado**: Secuencia perfecta: solicitud → parámetros → cálculo → resultado

### 🎯 Experiencia de usuario mejorada
- **Cálculos más fluidos**: Eliminadas respuestas inesperadas durante entrada de datos
- **Mensajes contextuales**: IA responde apropiadamente según el contexto de la conversación  
- **Resultados estructurados**: Todos los cálculos se muestran en formato organizado en console blocks
- **Coherencia conversacional**: Fix de loops de respuestas genéricas durante fórmulas activas

## [1.4.5] - 2025-08-27
### 🚀 Sistema completo de auto-inicio del backend en producción
- **Auto-inicio funcionando**: Backend se inicia automáticamente al abrir la aplicación instalada
- **Script batch optimizado**: Comando con rutas corregidas para espacios en nombres de carpetas
- **CMD visible para diagnóstico**: Ventana de terminal visible durante desarrollo para monitoreo
- **Gestión de procesos**: Control completo del ciclo de vida del backend desde Electron

### 📊 Barra de progreso mejorada y optimizada  
- **Progreso lineal**: Cambio de "Paso 1 de 4" a progreso limpio de 0-100%
- **Números redondeados**: Eliminados decimales innecesarios (14% en lugar de 13.9566666%)
- **Timing inteligente**: Espera 30 segundos antes de mostrar errores reales
- **Estados progresivos**: "Iniciando backend..." → "Cargando Python..." → "Preparando modelo..."

### ⚡ Optimización del polling y logging
- **Polling adaptativo**: Intervalos dinámicos según estado (60s cuando ready, 15s en error)
- **Logging reducido**: 95% menos logs de /ping en CMD (solo cada 30 segundos)
- **Mejor rendimiento**: Menor consumo de CPU y red durante operación normal

### 🔧 Sincronización de versiones
- **Versiones consistentes**: VERSION.txt, package.json y Settings.tsx sincronizados en 1.4.5
- **Instalador limpio**: Solo una versión final sin archivos de desarrollo
- **Corrección de rutas**: Manejo apropiado de espacios en rutas de instalación Windows

## [1.4.4] - 2025-08-13
### 🐛 Corrección crítica del ciclo infinito en composición corporal
- **Fix ciclo infinito**: Resuelto bug donde sistema preguntaba repetidamente los mismos parámetros
- **Mejora en recolección progresiva**: Ahora analiza TODA la conversación en lugar de solo las últimas 15 líneas
- **Debug logging**: Sistema completo de logs para monitoreo en tiempo real de detección de fórmulas
- **Validación robusta**: Prevención de pérdida de parámetros en conversaciones largas
- **Optimización de memoria**: Mantiene contexto completo sin degradación de rendimiento

### 🎯 Mejoras en detección de parámetros médicos
- **Extracción mejorada**: Algoritmos más precisos para peso, altura, edad, sexo y pliegues cutáneos
- **Persistencia de datos**: Los parámetros ya ingresados no se pierden durante la conversación
- **Validación inteligente**: Rangos de valores apropiados para cada medida antropométrica
- **Compatibilidad de unidades**: Soporte automático para kg/cm/mm en diferentes formatos

### 🔧 Optimizaciones técnicas del backend
- **Análisis contextual completo**: Procesamiento de toda la conversación para recolección progresiva
- **Prevención de contaminación**: Separación clara entre nuevas solicitudes y recolección de datos
- **Logging estructurado**: Trazabilidad completa del flujo de detección y cálculo de fórmulas

## [1.4.3] - 2025-08-12
### 🧠 Sistema inteligente de detección y descarga del modelo IA
- **Detección automática del modelo**: Estado en tiempo real (not_downloaded, loading, ready, error)
- **UX de descarga profesional**: Splash screen elegante con progreso visual
- **Estimación de tiempo**: Cálculo dinámico del tiempo restante de descarga
- **Velocidad en tiempo real**: Monitoreo de velocidad de descarga (MB/s)
- **Cancelación de descarga**: Posibilidad de cancelar y reintentar la descarga
- **Progreso visual**: Barra de progreso animada con efectos shimmer

### 🎨 Identidad visual personalizada
- **Loading personalizado**: Integración del logo de carga de Calyx AI
- **Componente reutilizable**: LoadingSpinner con múltiples tamaños (sm, md, lg, xl)
- **Consistencia de marca**: Reemplazo de iconos genéricos por diseño propio
- **Animaciones suaves**: Transiciones profesionales con Framer Motion

### 🔧 Nuevas funcionalidades técnicas
- **Hook useModelStatus**: Verificación automática del estado del modelo cada 10s
- **Hook useModelDownload**: Gestión completa del proceso de descarga
- **Endpoints del backend**: `/model/status`, `/model/download`, `/model/download/progress`
- **Detección de caché**: Verificación inteligente de modelos ya descargados
- **Información técnica**: Tamaño del modelo, dispositivo (GPU/CPU), velocidad

### 📱 Integración en la interfaz
- **Indicador en chat**: Estado del modelo en tiempo real en la página principal
- **Panel en configuraciones**: Información detallada con botón de descarga
- **Botones contextuales**: "Descargar modelo", "Reintentar", "Cancelar"
- **Mensajes educativos**: Información sobre privacidad y funcionamiento local

## [1.4.2] - 2025-08-11
### 🎨 Interfaz estilo ChatGPT con barra lateral y configuraciones
- **Barra lateral profesional**: Diseño similar a ChatGPT con navegación fluida
- **Sistema de configuraciones**: Página dedicada con secciones organizadas
- **Logo integrado**: Logo pequeño en la barra lateral junto al nombre "Calyx AI"
- **Navegación mejorada**: Botón hamburguesa para abrir/cerrar menú lateral
- **Información detallada del modelo**: "Phi-3-mini-4k-instruct (Local)" en lugar de solo "Local"

### 🚀 Nuevas funcionalidades
- **"Nuevo chat"**: Opción para limpiar conversación actual
- **"Configuraciones"**: Acceso centralizado a todas las opciones
- **Switch de tema integrado**: Toggle profesional dentro de configuraciones
- **Información del sistema**: Versión, modelo de IA y desarrolladores
- **Diseño responsive**: Adaptable a móviles y desktop

### 🔧 Mejoras técnicas
- **Context API**: Sistema de navegación entre vistas (chat/settings)
- **Componentes modulares**: Sidebar, MenuButton, SettingsPage separados
- **ThemeToggle mejorado**: Variantes floating e inline
- **Gestión de estado**: Control de apertura/cierre de sidebar
- **Overlays responsivos**: Comportamiento diferente en móvil vs desktop

### 🎯 Experiencia de usuario
- **Navegación intuitiva**: Patrones familiares de aplicaciones modernas
- **Transiciones suaves**: Animaciones en todas las interacciones
- **Accesibilidad mejorada**: Títulos descriptivos y botones claramente identificados
- **Identidad visual**: Logo consistente en toda la aplicación

## [1.4.1] - 2025-08-10
### ⚡ Mejoras de velocidad y autoscroll
- **Velocidad de escritura mejorada**: Aumentada 100% la velocidad de animación en consola (50ms → 25ms)
- **Parpadeo de cursor optimizado**: Velocidad de parpadeo aumentada 100% (500ms → 250ms)
- **Autoscroll inteligente**: 
  - Scroll automático cuando se agregan nuevos mensajes al chat
  - Scroll en tiempo real durante la animación de escritura de la consola
  - Comportamiento suave y natural para mejor experiencia de usuario
- **Experiencia de chat fluida**: Ya no es necesario hacer scroll manual para ver mensajes nuevos

### 🔧 Mejoras técnicas
- **Chat.tsx**: Implementado `useRef` y `useEffect` para autoscroll automático
- **ConsoleBlock.tsx**: Agregado scroll en tiempo real durante animación de `TerminalTypewriter`
- **Scroll suave**: Utilizando `scrollIntoView({ behavior: "smooth" })` para transiciones fluidas

## [1.4.0] - 2025-08-03
### 🎯 Correcciones críticas de separación de fórmulas médicas
- **SOLUCIONADO: Problema de reutilización de parámetros entre fórmulas**: Ahora el sistema distingue correctamente entre nuevas solicitudes de fórmulas y recolección progresiva de parámetros
- **SOLUCIONADO: Error "user: 65" al responder preguntas**: El frontend ahora mantiene contexto extendido (20 mensajes) para fórmulas médicas en lugar de 6 mensajes
- **Separación inteligente de contexto**: 
  - Nueva solicitud de fórmula (ej: "composición corporal") → Limpia parámetros anteriores
  - Respuesta simple (ej: "65", "M", "25") → Continúa recolección progresiva
- **Detección mejorada de fórmulas en progreso**: Reconoce preguntas específicas como "pliegue cutáneo", "circunferencia del brazo" para mantener contexto de composición corporal

### 🔧 Mejoras técnicas
- **Lógica de detección de nueva solicitud**: Diferencia entre palabras clave de fórmulas y respuestas numéricas/de texto
- **Contexto adaptativo en frontend**: Automáticamente extiende el contexto cuando detecta conversaciones de fórmulas médicas
- **Logging mejorado**: Mejor trazabilidad del proceso de detección de fórmulas y extracción de parámetros
- **Tests automatizados**: Nuevos tests para verificar separación de fórmulas y recolección progresiva

### 🏥 Experiencia de usuario
- **Flujo natural entre fórmulas**: Ahora puedes calcular IMC y luego solicitar composición corporal sin interferencias
- **Recolección progresiva confiable**: Las respuestas a preguntas de parámetros se acumulan correctamente
- **Eliminación de preguntas repetitivas**: No volverá a preguntar por peso/altura cuando cambies de IMC a composición corporal

### ⚡ Rendimiento
- **Contexto optimizado**: Solo usa contexto extendido cuando es necesario (fórmulas médicas)
- **Detección más rápida**: Algoritmo mejorado para identificar tipo de mensaje (nueva fórmula vs respuesta)

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
