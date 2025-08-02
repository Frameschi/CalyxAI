
# Calyx AI

Calyx AI es una aplicación de nutrición inteligente que funciona completamente de forma local, combinando una interfaz moderna (Electron + React) con un backend robusto (FastAPI + modelo Phi-3-Mini-4K-Instruct en GPU y SQLite). Permite consultas de alimentos, cálculos nutricionales automáticos y chat asistente general, sin depender de la nube.

## Objetivo
Ofrecer una herramienta de consulta nutricional y asistente personal, rápida, privada y sin conexión, ideal para profesionales, estudiantes y usuarios preocupados por su alimentación.

## Características
- Chat con IA local (modelo Phi-3 Mini 4K Instruct, 4-bit, GPU)
- **Cálculos automáticos de fórmulas nutricionales** (IMC, TMB, etc.)
- **Consola técnica animada** para mostrar procesos de cálculo paso a paso
- **Conversión automática de unidades** (175cm ↔ 1.75m, kg ↔ g)
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
- **Animación terminal profesional** con cursor único y efecto typewriter
- **Conversión de unidades robusta** para altura (cm/m) y peso (kg/g)
- Carga y uso de modelo Phi-3 Mini en GPU y 4-bit (bitsandbytes)
- Frontend con chat moderno, manejo de errores y timeouts
- Búsqueda de alimentos robusta, insensible a acentos y mayúsculas
- App de escritorio y web funcional (Electron y navegador)
- Pruebas exitosas de comunicación y generación de respuestas

---
Desarrollado por Frameschi. Versión 1.3.4

## Notas de versión
Consulta los cambios recientes en [CHANGELOG.md](./CHANGELOG.md)
