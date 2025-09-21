# Calyx AI - AI Coding Agent Instructions

## Project Overview
Calyx AI is a **nutrition intelligence application** combining a modern Electron + React frontend with a robust FastAPI backend featuring **Qwen2.5-3B with GPU optimization**. The app provides local nutrition consultations, automatic medical calculations, and chat assistance without external dependencies.

## Architecture Overview

### AI System
- **Qwen2.5-3B**: Advanced language model loaded via HuggingFace Transformers with 4-bit quantization on GPU, optimized for medical and nutritional calculations
- **Dynamic Switching**: Automatic model selection based on query complexity (nutrition chat vs. medical formulas)
- **GPU Optimization**: 42%/58% CPU/GPU balance with 4-bit quantization for efficient VRAM usage

### Backend (FastAPI + Python)
- **Core Engine**: `ai_engine.py` manages model loading and inference
- **Nutrition System**: SQLite database (`datainfo.db`) with accent-insensitive food search
- **Medical Formulas**: JSON-driven (`data_formulas.json`) progressive parameter collection
- **Endpoints**: `/chat`, `/alimento`, `/health`, `/ping` with CORS enabled for frontend

### Frontend (Electron + React + TypeScript)
- **UI Framework**: React with TypeScript, Tailwind CSS, Framer Motion animations
- **Desktop App**: Electron with auto-starting backend in production builds
- **Key Components**: Animated console blocks, model status management, and calculation displays
- **State Management**: Context-based model status polling, animation state tracking

## Critical Developer Workflows

### Development Setup
```bash
# Backend (manual start required)
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -m requirements.txt
python main.py

# Frontend (separate terminal)
cd frontend
npm install
npm run dev  # Runs on http://localhost:5173
```

### Build & Deployment
```bash
# Development build
npm run build-app

# Production installer (Windows)
npm run dist-windows

# Full distribution
npm run dist
```

### Model Management
- Models load automatically on backend startup
- Switching occurs dynamically based on query analysis
- GPU memory optimization critical for performance
- Fallback messages when models unavailable

## Project-Specific Patterns & Conventions

### Progressive Parameter Collection
Medical formulas use conversational parameter gathering:
```python
# Pattern: Check last 3 lines only for active formulas
formula_en_progreso = any(
    pregunta in mensaje_ai for pregunta in [
        "cuál es tu peso en kg", "cuál es tu altura en metros", 
        "cuántos años tienes", "eres hombre o mujer"
    ]
)
```

### Unit Conversion System
Automatic handling of mixed units:
```python
# Examples: 175cm → 1.75m, 70kg → 70000g
factor = (cantidad_detectada / cantidad_base) if cantidad_detectada else 1.0
```

### Console Block Animations
All calculations display in animated console blocks with typewriter effect:
```typescript
// Pattern: Results go to console blocks, not chat messages
<ConsoleBlock title="Cálculo IMC" input={params} output={result} />
```

### Accent-Insensitive Search
Food database queries remove accents for flexible matching:
```python
def quitar_acentos(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto) 
                   if unicodedata.category(c) != 'Mn')
```

### Category-Based Nutrition Fields
Food results show relevant fields based on category:
```python
campos_por_categoria = {
    "verduras": ["cantidad", "energia (kcal)", "fibra (g)"],
    "cereales": ["cantidad", "energia (kcal)", "hidratos de carbono (g)"],
    "aoa": ["cantidad", "energia (kcal)", "proteina (g)"],
    # ... etc
}
```

## Integration Points & Dependencies

### External Services
- **HuggingFace**: Qwen2.5-3B model downloads and tokenization via Transformers
- **SQLite**: Local databases for food data and user data

### Cross-Component Communication
- **Backend Status**: Polling `/health` endpoint for model readiness
- **CORS**: Configured for `http://localhost:5173` development
- **Process Management**: Electron spawns Python backend in production

### Error Handling Patterns
- **Timeout Management**: 30-second waits before showing errors
- **Fallback Messages**: Context-aware responses when models fail
- **Graceful Degradation**: App continues with limited functionality

## Key Files & Directories

### Backend Core
- `backend/main.py`: FastAPI server, endpoints, formula logic
- `backend/ai_engine.py`: Dual model management and inference
- `backend/data_formulas.json`: Medical calculation definitions
- `backend/datainfo.db`: Nutrition database (accent-insensitive queries)

### Frontend Core
- `frontend/src/pages/Chat.tsx`: Main chat interface with model switching
- `frontend/src/components/ConsoleRenderer.tsx`: Animated calculation displays
- `frontend/src/components/ThinkingDropdown.tsx`: Qwen2.5-3B reasoning transparency
- `frontend/electron/main.cjs`: Desktop app lifecycle and backend spawning

### Configuration
- `frontend/package.json`: Build scripts and Electron configuration
- `backend/requirements.txt`: Python dependencies (FastAPI, transformers, torch)
- `frontend/tsconfig.json`: TypeScript configuration for React components

## Development Best Practices

### Code Organization
- **Separation of Concerns**: Backend handles AI/ML, frontend manages UI/UX
- **Modular Architecture**: Clear boundaries between nutrition, chat, and calculation systems
- **Error Resilience**: Comprehensive fallbacks for model failures and network issues

### Performance Considerations
- **GPU Memory**: Critical optimization for 4GB VRAM systems
- **Lazy Loading**: Models load on-demand, not at import time
- **Polling Optimization**: Adaptive intervals based on backend state

### Testing Approach
- **Integration Focus**: End-to-end testing of AI responses and calculations
- **Model Validation**: Verify Qwen2.5-3B outputs and calculation accuracy
- **UI Animation Testing**: Console block rendering and thinking dropdown behavior

## Common Pitfalls to Avoid

### Model Loading Issues
- Always check GPU availability before quantization
- Handle Transformers loading failures gracefully
- Provide clear error messages for model initialization

### Formula Context Management
- Maintain conversation history for multi-step calculations
- Avoid parameter contamination between different formulas
- Preserve context for 20 messages (medical) vs 6 messages (chat)

### Build Configuration
- Ensure correct paths for Windows installer generation
- Maintain version consistency across `package.json`, `VERSION.txt`, and settings
- Handle spaces in installation paths properly

## AI Agent Guidelines

When working on Calyx AI:

1. **Optimize Qwen2.5-3B**: Focus on efficient GPU utilization and model performance
2. **Test Model Features**: Validate features work with Qwen2.5-3B for nutrition and medical calculations
3. **Maintain UI Polish**: Console animations and thinking transparency are core UX features
4. **Handle Internationalization**: Spanish UI with accent-insensitive search patterns
5. **Optimize Performance**: GPU utilization and memory management are critical
6. **Follow Progressive UX**: Parameter collection should feel conversational and natural

This codebase represents a sophisticated local AI application with professional UX patterns. Focus on maintaining the balance between powerful AI capabilities and smooth user experience.