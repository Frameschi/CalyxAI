
import React, { useState, useRef, useEffect } from "react";
import { Send, ChevronDown } from "lucide-react";
import { ConsoleRenderer } from "../components/ConsoleRenderer";
import { ConsoleBlockYaml } from "../components/ConsoleBlockYaml";
import { esBloqueYaml } from "../utils/formatConsole";
import { Sidebar } from "../components/Sidebar";
import { SettingsPage } from "./Settings";
import { useModelStatus } from "../contexts/ModelStatusContext";
import BackendStartupProgress from "../components/BackendStartupProgress";
import ThinkingDropdown from "../components/ThinkingDropdown";
import AiOrb from "../components/AiOrb";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function Chat() {
  interface Message {
    from: "ai" | "user";
    text?: string;
    type: "text" | "yaml" | "console";
    title?: string;
    input?: string;
    output?: string;
    thinking?: string;
  }

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeAnimations, setActiveAnimations] = useState(0); // Contador de animaciones activas
  const [currentView, setCurrentView] = useState<'chat' | 'settings'>('chat');
  const [showBackendProgress, setShowBackendProgress] = useState(true);
  const [selectedModel, setSelectedModel] = useState("phi3-mini");
  const [modelSwitching, setModelSwitching] = useState(false);
  const [availableModels, setAvailableModels] = useState<Record<string, string>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null); // Nueva referencia para el input
  
  // Hook para verificar el estado del modelo
  const { modelStatus, isLoading: modelLoading, error: modelError } = useModelStatus();
  
  // Estado combinado para deshabilitar input
  const isProcessing = loading || activeAnimations > 0 || modelSwitching;
  
  // Detectar si hay mensajes para determinar posición del orb
  const hasMessages = messages.length > 0;
  const hasAiMessages = messages.filter(msg => msg.from === "ai").length > 0;
  
  // Estados para manejar la transición del orb
  const [isOrbTransitioning, setIsOrbTransitioning] = useState(false);
  const [showCenterOrb, setShowCenterOrb] = useState(true);
  const [showLateralOrb, setShowLateralOrb] = useState(false);
  
  // Funciones para manejar estado de animaciones
  const handleTypingStart = () => {
    setActiveAnimations(prev => prev + 1);
  };
  
  const handleTypingEnd = () => {
    setActiveAnimations(prev => Math.max(0, prev - 1));
  };

  // Efecto para manejar el estado inicial de los orbs
  useEffect(() => {
    if (hasMessages) {
      // Si ya hay mensajes, mostrar orb lateral
      setShowCenterOrb(false);
      setShowLateralOrb(true);
    } else {
      // Si no hay mensajes, mostrar orb central
      setShowCenterOrb(true);
      setShowLateralOrb(false);
    }
  }, [hasMessages]);

  // Función para cargar información del modelo actual
  const loadCurrentModel = async () => {
    try {
      const response = await fetch(`${API_URL}/model/current`);
      if (response.ok) {
        const data = await response.json();
        setSelectedModel(data.key);
        setAvailableModels(data.available_models || {});
      }
    } catch (error) {
      console.error("Error cargando modelo actual:", error);
    }
  };

  // Función para cambiar modelo
  const handleModelChange = async (newModelKey: string) => {
    if (newModelKey === selectedModel || modelSwitching) return;
    
    setModelSwitching(true);
    try {
      const response = await fetch(`${API_URL}/model/switch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ model_key: newModelKey }),
      });
      
      if (response.ok) {
        const data = await response.json();
        setSelectedModel(newModelKey);
      } else {
        const errorData = await response.json();
        console.error("Error cambiando modelo:", errorData.error);
        // Mostrar error en el chat
        setMessages(prev => [...prev, {
          from: "ai", 
          text: `Error al cambiar modelo: ${errorData.error}`,
          type: "text"
        }]);
      }
    } catch (error) {
      console.error("Error de conexión al cambiar modelo:", error);
      setMessages(prev => [...prev, {
        from: "ai",
        text: "Error de conexión al cambiar modelo. Verifica que el backend esté funcionando.",
        type: "text"
      }]);
    } finally {
      setModelSwitching(false);
    }
  };

  // Auto scroll cuando se agregan mensajes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto focus en el input cuando se carga la página
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Cargar información del modelo actual al iniciar
  useEffect(() => {
    loadCurrentModel();
  }, []);

  const handleSend = async () => {
    if (input.trim() === "" || isProcessing) return; // Usar isProcessing en lugar de solo loading
    
    const userMsg = input;
    const isFirstMessage = messages.length === 0;
    
    // Activar transición del orb si es el primer mensaje
    if (isFirstMessage) {
      setIsOrbTransitioning(true);
      setShowCenterOrb(false);
      
      // Después de 1200ms mostrar el orb lateral (coincide con duración CSS)
      setTimeout(() => {
        setShowLateralOrb(true);
        setIsOrbTransitioning(false);
      }, 1200);
    }
    
    setMessages([...messages, { from: "user", text: userMsg, type: "text" }]);
    setInput("");
    setLoading(true);
    
    // Reenfoque automático del input después de un breve delay para permitir que React actualice el estado
    setTimeout(() => {
      inputRef.current?.focus();
    }, 100);
    
    try {
      // Usar IA general con herramientas para todas las consultas
      try {
        // CRÍTICO: Mantener contexto más amplio para fórmulas médicas
        // Las fórmulas médicas pueden requerir muchos intercambios (hasta 18 mensajes para composición corporal)
        
        // Detectar si estamos en una conversación de fórmula médica
        const esFamilaMedica = messages.some(m => 
          m.text && (
            m.text.toLowerCase().includes('imc') ||
            m.text.toLowerCase().includes('composicion corporal') ||
            m.text.toLowerCase().includes('composición corporal') ||
            m.text.toLowerCase().includes('peso en kg') ||
            m.text.toLowerCase().includes('altura en metros') ||
            m.text.toLowerCase().includes('años tienes') ||
            m.text.toLowerCase().includes('pliegue cutáneo') ||
            m.text.toLowerCase().includes('circunferencia')
          )
        );
        
        // Usar contexto extendido para fórmulas médicas, normal para otras consultas
        const cantidadContexto = esFamilaMedica ? 20 : 6;
        const contexto = messages.slice(-cantidadContexto).map((m: Message) => `${m.from}: ${m.text}`).join('\n');
        const promptFinal = `${contexto}\nuser: ${userMsg}`;
        
        console.log(`[DEBUG Frontend] Es fórmula médica: ${esFamilaMedica}, Contexto: ${cantidadContexto} mensajes`);
        
        const controller = window.AbortController ? new window.AbortController() : new AbortController();
        const timeoutId = window.setTimeout(() => {
          console.log('[DEBUG Frontend] Timeout alcanzado, abortando petición');
          controller.abort();
        }, 600000); // 10 minutos para Qwen2.5-3B
        
        console.log(`[DEBUG Frontend] Iniciando fetch a ${API_URL}/chat con timeout de 10 minutos`);
        console.log(`[DEBUG Frontend] Prompt length: ${promptFinal.length} caracteres`);
        
        try {
          const res = await fetch(`${API_URL}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: promptFinal }),
            signal: controller.signal
          });
          
          console.log(`[DEBUG Frontend] Fetch completado, status: ${res.status}`);
          window.clearTimeout(timeoutId);
          console.log('[DEBUG Frontend] Timeout limpiado exitosamente');
          
          const data = await res.json();
          console.log(`[DEBUG Frontend] JSON parseado exitosamente, data keys: ${Object.keys(data)}`);
          // Procesar bloque técnico si existe
          let arr: Message[] = [];
          if (data.message && data.message.trim().length > 0) {
            const tipo = esBloqueYaml(data.message) ? "yaml" : "text";
            const mensaje: Message = { 
              from: "ai", 
              text: data.message, 
              type: tipo 
            };
            
            // Incluir thinking solo si existe en la respuesta
            if (data.thinking && data.thinking.trim().length > 0) {
              mensaje.thinking = data.thinking;
            }
            
            arr.push(mensaje);
          }
          if (data.console_block && typeof data.console_block === 'object') {
            arr.push({
              from: "ai",
              type: "console",
              title: data.console_block?.title || "",
              input: data.console_block?.input || "",
              output: data.console_block?.output || ""
            });
          }
          if (arr.length === 0) {
            arr.push({ from: "ai", text: "(Sin respuesta)", type: "text" });
          }
          setMessages((msgs: Message[]) => [...msgs, ...arr]);
        } catch (err: any) {
          window.clearTimeout(timeoutId);
          console.log('[DEBUG Frontend] Error en fetch, limpiando timeout');
          console.log(`[DEBUG Frontend] Error type: ${err?.name}, message: ${err?.message}`);
          
          if (err && err.name === 'AbortError') {
            console.log('[DEBUG Frontend] AbortError detectado - verificando si fue por timeout o cancelación manual');
            setMessages((msgs: Message[]) => [...msgs, { from: "ai", text: "El servidor está tardando demasiado en responder. Intenta de nuevo más tarde.", type: "text" }]);
          } else {
            console.log('[DEBUG Frontend] Error de conexión que no es AbortError');
            setMessages((msgs: Message[]) => [...msgs, { from: "ai", text: "Error de conexión con el backend.", type: "text" }]);
          }
        }
      } catch (err) {
        setMessages((msgs: Message[]) => [...msgs, { from: "ai", text: "Error inesperado en el frontend.", type: "text" }]);
      }
    } finally {
      setLoading(false);
      
      // Reenfoque automático del input cuando termine el procesamiento
      setTimeout(() => {
        inputRef.current?.focus();
      }, 200);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
  };

  const handleOpenSettings = () => {
    setCurrentView('settings');
  };

  const handleBackToChat = () => {
    setCurrentView('chat');
  };

  // Si estamos en configuraciones, mostrar esa página
  if (currentView === 'settings') {
    return <SettingsPage onBack={handleBackToChat} />;
  }

  return (
    <div className="flex h-screen bg-white dark:bg-gray-900 transition-colors">
      {/* Sidebar fija */}
      <Sidebar
        onNewChat={handleNewChat}
        onOpenSettings={handleOpenSettings}
      />
      
      {/* Main content area */}
      <div className="flex-1 flex flex-col ml-80">
        {/* Selector de modelo en la parte superior */}
        <div className="p-4">
          <div className="flex items-center">
            <label htmlFor="model-select" className="text-sm font-medium text-gray-700 dark:text-gray-300 mr-3">
              Modelo:
            </label>
            <div className="relative">
              <select
                id="model-select"
                value={selectedModel}
                onChange={(e) => handleModelChange(e.target.value)}
                disabled={isProcessing}
                className={`bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors appearance-none ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'} min-w-80`}
              >
                {Object.entries(availableModels).map(([key, description]) => (
                  <option key={key} value={key}>
                    {description}
                  </option>
                ))}
              </select>
              <ChevronDown 
                size={16} 
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 dark:text-gray-400 pointer-events-none" 
              />
            </div>
            {modelSwitching && (
              <span className="text-xs text-blue-600 dark:text-blue-400 ml-3 flex items-center gap-1">
                <img 
                  src="/loading.png" 
                  alt="Loading" 
                  className="w-4 h-4 animate-spin" 
                />
                Cambiando modelo...
              </span>
            )}
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-6">
        {/* Pantalla de bienvenida cuando no hay mensajes */}
        {messages.length === 0 && (
          <div className="flex-1 flex items-center justify-center min-h-96">
            <div className="text-center space-y-6 max-w-md relative">
              {/* ORB CENTRAL - alineado y centrado arriba del título */}
              {!showBackendProgress && !modelError && showCenterOrb && (
                <div style={{ position: 'absolute', left: '50%', top: '40px', transform: 'translateX(-50%)' }}>
                  <AiOrb 
                    size="large" 
                    isActive={modelSwitching}
                    position="center"
                    isTransitioning={isOrbTransitioning}
                  />
                </div>
              )}
              <h2
                className="text-4xl font-extrabold text-gray-800 dark:text-white"
                style={{ marginTop: '100px', fontFamily: 'Cormorant Garamond, serif', fontWeight: 800, letterSpacing: '0.01em' }}
              >
                Bienvenido a Calyx AI
              </h2>
              {/* Mostrar progreso del backend si está iniciándose */}
              {showBackendProgress && (
                <BackendStartupProgress 
                  onReady={() => setShowBackendProgress(false)}
                  className="max-w-md mx-auto"
                />
              )}
              {/* Mensaje adicional si hay error de conexión (solo cuando no se muestra progreso) */}
              {!showBackendProgress && modelError && (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                  <p className="text-red-700 dark:text-red-300 text-sm">
                    No se puede conectar con el backend. Asegúrate de que el servidor esté ejecutándose en el puerto 8000.
                  </p>
                </div>
              )}
              <p className="text-gray-600 dark:text-gray-300 text-center">
                ¿En qué puedo asistirte hoy?
              </p>
            </div>
          </div>
        )}
        
        {messages.map((msg: any, i: number) => {
          if (msg.from === "user") {
            return (
              <div
                key={i}
                className="mb-4 flex justify-end"
              >
                <div className="bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white px-4 py-2 rounded-2xl max-w-lg shadow border border-gray-300 dark:border-gray-600 transition-colors">
                  {msg.text}
                </div>
              </div>
            );
          } else if (msg.type === "yaml") {
            return <ConsoleBlockYaml key={i} input={msg.text} />;
          } else if (msg.type === "console") {
            return (
              <div key={i} className="mb-4">
                <div className="flex justify-start">
                  <ConsoleRenderer 
                    title={msg.title} 
                    input={msg.input} 
                    output={msg.output} 
                    onTypingStart={handleTypingStart}
                    onTypingEnd={handleTypingEnd}
                  />
                </div>
                {/* SIN ORB AQUÍ - movido al final */}
              </div>
            );
          } else {
            return (
              <div key={i} className="mb-4">
                <div className="flex justify-start">
                  <div className="max-w-4xl">
                    {/* Mostrar ThinkingDropdown solo si hay thinking content */}
                    {msg.thinking && (
                      <ThinkingDropdown 
                        thinking={msg.thinking} 
                        className="mb-2" 
                      />
                    )}
                    <ConsoleRenderer text={msg.text} />
                  </div>
                </div>
              </div>
            );
          }
        })}
        
        {/* UN SOLO ORB LATERAL - Al final de todos los mensajes */}
        {hasMessages && showLateralOrb && (
          <div className="mb-4 flex justify-start items-start">
            <div className="mr-3 mt-1 flex-shrink-0">
              <AiOrb 
                size="medium" 
                isActive={isProcessing}
                position="lateral"
              />
            </div>
            {loading && (
              <div className="max-w-4xl">
                <div className="text-gray-500 dark:text-gray-400 italic">
                  {selectedModel === 'qwen2.5-3b' ? "Analizando con IA avanzada..." : "Procesando respuesta..."}
                </div>
              </div>
            )}
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Indicador de estado del modelo (solo cuando hay mensajes) */}
      {messages.length > 0 && (
        <div className="px-6 pb-2">
        </div>
      )}
      
      <div className="p-6 bg-transparent">
        {/* Input de chat */}
        <div className="flex items-center border border-gray-300 dark:border-gray-600 rounded-2xl px-4 py-2 shadow-md bg-white dark:bg-gray-800 transition-colors">
          <input
            ref={inputRef}
            type="text"
            className={`flex-1 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 outline-none border-none text-base py-2 transition-colors ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
            placeholder={
              modelSwitching ? "⟳ Cambiando modelo..." :
              loading ? (selectedModel === 'qwen2.5-3b' ? "� Analizando con IA avanzada..." : "Procesando respuesta...") : 
              activeAnimations > 0 ? "Desglosando cálculos..." : 
              "Escribe tu mensaje..."
            }
            value={input}
            onChange={e => !isProcessing && setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !isProcessing && handleSend()}
            disabled={isProcessing}
          />
          <button
            onClick={handleSend}
            className={`ml-2 bg-white dark:bg-gray-700 rounded-full p-0 hover:bg-gray-100 dark:hover:bg-gray-600 transition-all flex items-center justify-center border border-gray-300 dark:border-gray-600 shadow ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
            aria-label="Enviar"
            style={{ width: 56, height: 56 }}
            disabled={isProcessing}
          >
            <Send size={28} className="text-gray-900 dark:text-white rotate-45 mx-auto block" strokeWidth={2.2} />
          </button>
        </div>
      </div>
      </div>
    </div>
  );
}
