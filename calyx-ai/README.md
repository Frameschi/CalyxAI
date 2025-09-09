
# Calyx AI

Calyx AI es una aplicación de nutrición inteligente que funciona completamente de forma local, combinando una interfaz moderna (Electron + React) con un backend robusto (FastAPI + **sistema dual de modelos IA** optimizado para GPU). Permite consultas de alimentos, cálculos nutricionales automáticos y chat asistente general con **capacidades de razonamiento avanzado**, sin depender de la nube.

## Objetivo
Ofrecer una herramienta de consulta nutricional y asistente personal, rápida, privada y sin conexión, ideal para profesionales, estudiantes y usuarios preocupados por su alimentación, con **análisis profundo** y **transparencia en el proceso de pensamiento**.

## Características principales
- **Dual AI System**: Phi-3-Mini (rápido) + **DeepSeek-R1** (razonamiento profundo)
- **🧠 Thinking Transparency**: Dropdown estilo ChatGPT mostrando el proceso de razonamiento completo
- **⚡ GPU Optimizado**: 42%/58% CPU/GPU balance para máximo rendimiento
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
- **Sistema de fórmulas automático** con detección inteligente de parámetros
- **Separación perfecta entre fórmulas** - IMC y Composición Corporal independientes
- **Contexto inteligente** - 20 mensajes para fórmulas médicas, 6 para chat general
- **Animación terminal profesional** con cursor único y efecto typewriter
- **Conversión de unidades robusta** para altura (cm/m) y peso (kg/g)
- Carga y uso de modelo Phi-3 Mini en GPU y 4-bit (bitsandbytes)
- Frontend con chat moderno, manejo de errores y timeouts
- Búsqueda de alimentos robusta, insensible a acentos y mayúsculas
- App de escritorio y web funcional (Electron y navegador)
- Pruebas exitosas de comunicación y generación de respuestas

---
Desarrollado por Frameschi. Versión 1.4.0

## Notas de versión
Consulta los cambios recientes en [CHANGELOG.md](./CHANGELOG.md)
