
# Calyx AI

Calyx AI es una aplicación de nutrición inteligente que funciona completamente de forma local, combinando una interfaz moderna (Electron + React) con un backend robusto (FastAPI + **Qwen2.5-3B optimizado para GPU**). Permite consultas de alimentos, cálculos nutricionales automáticos y chat asistente general con **capacidades de razonamiento avanzado**, sin depender de la nube.

## Objetivo
Ofrecer una herramienta de consulta nutricional y asistente personal, rápida, privada y sin conexión, ideal para profesionales, estudiantes y usuarios preocupados por su alimentación, con **análisis profundo** y **transparencia en el proceso de pensamiento**.

## Características principales
- **Qwen2.5-3B Exclusivo**: Modelo de lenguaje avanzado con cuantización 4-bit optimizada para GPU
- **🧠 Thinking Transparency**: Dropdown estilo ChatGPT mostrando el proceso de razonamiento completo
- **⚡ GPU Optimizado**: 42%/58% CPU/GPU balance para máximo rendimiento en GTX 1050 Ti
- **🤖 Sistema Híbrido de IA**: 3 prompts especializados con detección automática inteligente
  - **Conversacional**: Interacciones sociales y consultas generales
  - **Nutricional**: Consultas de alimentos con herramientas de base de datos y **tablas Markdown profesionales**
  - **Médico**: Cálculos automáticos con formato profesional
- **📊 Tablas Nutricionales Profesionales**: Renderizado Markdown completo con bordes reales y formato ChatGPT
- **Cálculos automáticos de fórmulas nutricionales** (IMC, Composición Corporal, TMB, etc.)
- **Separación inteligente de fórmulas médicas** - No interfieren entre sí
- **Recolección progresiva de parámetros** - Conversaciones naturales para obtener datos
- **Consola técnica animada** para mostrar procesos de cálculo paso a paso
- **Conversión automática de unidades** (175cm ↔ 1.75m, kg ↔ g)
- **Contexto adaptativo** - Mantiene historial extendido para fórmulas médicas complejas
- Búsqueda flexible de alimentos y datos nutricionales desde base SQLite
- Interfaz moderna y responsiva (Electron, React, Tailwind)
- Funciona como app de escritorio y web
- Manejo robusto de errores y timeouts (el chat nunca se congela)
- Modularidad para cambiar o agregar modelos IA fácilmente
- Backend y frontend desacoplados
- Sin dependencia de servicios externos

## Logros actuales
- Backend FastAPI modularizado, con IA y base de datos integrados
- **Sistema híbrido de IA con 3 prompts especializados** (conversacional, nutricional, médico)
- **Detección automática inteligente** de tipo de consulta y aplicación del prompt apropiado
- **Sistema Markdown profesional** para respuestas nutricionales con tablas de calidad ChatGPT
- **Separación perfecta de tipos de respuesta** - nutricionales usan Markdown, técnicas usan bloques YAML
- **Sistema de fórmulas automático** con detección inteligente de parámetros
- **Separación perfecta entre fórmulas** - IMC y Composición Corporal independientes
- **Contexto inteligente** - 20 mensajes para fórmulas médicas, 6 para chat general
- **Animación terminal profesional** con cursor único y efecto typewriter
- **Conversión de unidades robusta** para altura (cm/m) y peso (kg/g)
- Carga y uso de modelo Qwen2.5-3B en GPU con cuantización 4-bit (Transformers + Accelerate)
- Frontend con chat moderno, manejo de errores y timeouts
- Búsqueda de alimentos robusta, insensible a acentos y mayúsculas
- App de escritorio y web funcional (Electron y navegador)
- Pruebas exitosas de comunicación y generación de respuestas

---
Desarrollado por Frameschi. Versión 1.7.3

## Sistema de Versiones

La versión de la aplicación se gestiona centralizadamente desde el archivo `VERSION.txt`. Para actualizar la versión:

1. **Edita `VERSION.txt`** con la nueva versión (ej: `1.8.0`)
2. **Ejecuta el script de sincronización:**
   ```bash
   python update_version.py
   ```
3. **Archivos actualizados automáticamente:**
   - `frontend/package.json`
   - `README.md`
4. **Archivos actualizados dinámicamente:**
   - `frontend/src/pages/Settings.tsx` (lee desde el backend)

---
Desarrollado por Frameschi. Versión 1.7.3

## Notas de versión
Consulta los cambios recientes en [CHANGELOG.md](./CHANGELOG.md)
