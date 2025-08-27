
import React, { useState, useRef, useEffect } from "react";
import { Send } from "lucide-react";
import { ConsoleRenderer } from "../components/ConsoleRenderer";
import { ConsoleBlockYaml } from "../components/ConsoleBlockYaml";
import { esBloqueYaml } from "../utils/formatConsole";
import { Sidebar } from "../components/Sidebar";
import { SettingsPage } from "./Settings";
import ModelStatusIndicator from "../components/ModelStatusIndicator";
import { useModelStatus } from "../hooks/useModelStatus";
import BackendStartupProgress from "../components/BackendStartupProgress";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function Chat() {
  interface Message {
    from: "ai" | "user";
    text?: string;
    type: "text" | "yaml" | "console";
    title?: string;
    input?: string;
    output?: string;
  }

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeAnimations, setActiveAnimations] = useState(0); // Contador de animaciones activas
  const [currentView, setCurrentView] = useState<'chat' | 'settings'>('chat');
  const [showBackendProgress, setShowBackendProgress] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null); // Nueva referencia para el input
  
  // Hook para verificar el estado del modelo
  const { modelStatus, isLoading: modelLoading, error: modelError } = useModelStatus();
  
  // Estado combinado para deshabilitar input
  const isProcessing = loading || activeAnimations > 0;
  
  // Funciones para manejar estado de animaciones
  const handleTypingStart = () => {
    setActiveAnimations(prev => prev + 1);
  };
  
  const handleTypingEnd = () => {
    setActiveAnimations(prev => Math.max(0, prev - 1));
  };

  // Auto scroll cuando se agregan mensajes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto focus en el input cuando se carga la página
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Palabras clave para detectar preguntas sobre alimentos
  const patronesAlimento = [
    /informaci[óo]n completa de ([a-zA-Záéíóúñ ]+)/i,
    /informaci[óo]n de ([a-zA-Záéíóúñ ]+)/i,
    /datos de ([a-zA-Záéíóúñ ]+)/i,
    /aporta ([a-zA-Záéíóúñ ]+)/i,
    /cu[aá]nt[ao]s? (?:calor[ií]as|prote[ií]nas|grasas|fibra|sodio) .* ([a-zA-Záéíóúñ ]+)/i
  ];

  const handleSend = async () => {
    if (input.trim() === "" || isProcessing) return; // Usar isProcessing en lugar de solo loading
    
    const userMsg = input;
    setMessages([...messages, { from: "user", text: userMsg, type: "text" }]);
    setInput("");
    setLoading(true);
    
    // Reenfoque automático del input después de un breve delay para permitir que React actualice el estado
    setTimeout(() => {
      inputRef.current?.focus();
    }, 100);
    
    try {
      // Detectar si la pregunta es sobre un alimento
      let alimentoDetectado = null;
      let esCompleta = false;
      for (const patron of patronesAlimento) {
        const match = userMsg.match(patron);
        if (match && match[1]) {
          alimentoDetectado = match[1].trim();
          if (/completa/i.test(userMsg)) esCompleta = true;
          break;
        }
      }

      if (alimentoDetectado) {
        // Consultar endpoint especializado
        try {
          const nombreParam = esCompleta ? `informacion completa de ${alimentoDetectado}` : alimentoDetectado;
          const res = await fetch(`${API_URL}/alimento?nombre=${encodeURIComponent(nombreParam)}`);
          const data = await res.json();
          if (data.error) {
            setMessages((msgs: Message[]) => [...msgs, { from: "ai", text: data.error, type: "text" }]);
          } else {
            let respuesta = '';
            if (data.mensaje) {
              respuesta += `🛈 ${data.mensaje}\n\n`;
            }
            let principal = null;
            if (data.filas && typeof data.filas === 'object') {
              principal = data.filas;
            } else if (data.info_completa && Array.isArray(data.info_completa)) {
              principal = data.info_completa;
            }
            let encabezado = `Información de ${alimentoDetectado}`;
            // Unidades conocidas para mostrar junto al valor
            const unidades: Record<string, string> = {
              "cantidad": "",
              "unidad": "",
              "energia": "kcal",
              "proteina": "g",
              "lipidos": "g",
              "hidratos de carbono": "g",
              "ag saturados": "g",
              "ag monoinsaturados": "g",
              "ag poliinsaturados": "g",
              "colesterol": "mg",
              "azucar": "g",
              "fibra": "g",
              "vitamina a": "mg re",
              "acido ascorbico": "mg",
              "acido folico": "mg",
              "calcio": "mg",
              "hierro": "mg",
              "potasio": "mg",
              "sodio": "mg",
              "fosforo": "mg",
              "etanol": "g",
              "ig": "",
              "carga glicemica": ""
            };
            function formatearDato(k: any, v: any): string {
              var kStr = (k === undefined || k === null) ? '' : String(k);
              var key = kStr.length > 0 ? kStr.charAt(0).toUpperCase() + kStr.slice(1) : '';
              var unidad = kStr && typeof kStr === 'string' ? (unidades[kStr.toLowerCase()] || "") : "";
              return key + ': ' + v + (unidad ? ' ' + unidad : '');
            }
            // Si es info completa, mostrar en YAML organizado
            if (principal && Array.isArray(principal) && nombreParam && nombreParam.toLowerCase().includes('completa')) {
              // Convertir array de objetos a un solo objeto plano para YAML, filtrando 'id'
              let objYaml: Record<string, any> = {};
              principal.forEach(function(item) {
                if (typeof item === 'object' && item !== null) {
                  Object.values(item).forEach(function(v) {
                    if (typeof v === 'string' && v.includes(':')) {
                      var partes = v.split(':');
                      if (partes.length >= 3) {
                        var clave = partes[1].trim();
                        var valor = partes.slice(2).join(':').trim();
                        if (clave.toLowerCase() !== 'id') objYaml[clave] = valor;
                      } else if (partes.length === 2) {
                        var clave2 = partes[0].replace(/^linea/i, '').trim();
                        var valor2 = partes[1].trim();
                        if (clave2.toLowerCase() !== 'id') objYaml[clave2] = valor2;
                      }
                    }
                  });
                }
              });
              // Mostrar encabezado y YAML robusto
              let yaml = `# ${encabezado}\n`;
              Object.entries(objYaml).forEach(([k, v]) => {
                yaml += `${k}: ${v}\n`;
              });
              setMessages(function(msgs) {
                let arr = msgs.concat([{ from: "ai", text: yaml, type: "yaml" }]);
                // Mostrar sugerencias como nota separada
                if (data.sugerencias && Array.isArray(data.sugerencias) && data.sugerencias.length > 0) {
                  arr = arr.concat([{ from: "ai", text: `Otras variantes: ${data.sugerencias.join(", ")}` , type: "text" }]);
                }
                return arr;
              });
            } else if (principal) {
              // Info básica: mostrar en texto organizado, no corrido
              respuesta += `${encabezado}:\n`;
              if (typeof principal === 'object' && !Array.isArray(principal)) {
                if (principal.clave && principal.valor) {
                  respuesta += '- ' + formatearDato(principal.clave, principal.valor) + '\n';
                } else {
                  Object.entries(principal).forEach(function(entry) {
                    var k = entry[0], v = entry[1];
                    if (["clave", "valor", "linea"].indexOf(k) === -1) {
                      respuesta += '- ' + formatearDato(k, v) + '\n';
                    }
                  });
                }
              } else if (Array.isArray(principal)) {
                principal.forEach(function(item) {
                  if (typeof item === 'object' && item !== null) {
                    Object.values(item).forEach(function(v) {
                      if (typeof v === 'string' && v.includes(':')) {
                        var partes = v.split(':');
                        if (partes.length >= 3) {
                          var clave = partes[1].trim();
                          var valor = partes.slice(2).join(':').trim();
                          respuesta += '- ' + clave.charAt(0).toUpperCase() + clave.slice(1) + ': ' + valor + '\n';
                        } else if (partes.length === 2) {
                          var clave2 = partes[0].replace(/^linea/i, '').trim();
                          var valor2 = partes[1].trim();
                          respuesta += '- ' + clave2.charAt(0).toUpperCase() + clave2.slice(1) + ': ' + valor2 + '\n';
                        } else {
                          respuesta += '- ' + v + '\n';
                        }
                      } else {
                        respuesta += '- ' + String(v) + '\n';
                      }
                    });
                    respuesta += '\n';
                  } else {
                    respuesta += String(item) + '\n';
                  }
                });
              }
              if (data.sugerencias && Array.isArray(data.sugerencias) && data.sugerencias.length > 0) {
                respuesta += `\nOtras variantes: ${data.sugerencias.join(", ")}`;
              }
              setMessages(function(msgs) { return msgs.concat([{ from: "ai", text: respuesta, type: "text" }]); });
            }
          }
        } catch (err) {
          setMessages((msgs: Message[]) => [...msgs, { from: "ai", text: "Error de conexión con el backend de alimentos.", type: "text" }]);
        }
        return;
      }

      // Si no es pregunta de alimento, usar IA general
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
        const timeoutId = window.setTimeout(() => controller.abort(), 60000);
        try {
          const res = await fetch(`${API_URL}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: promptFinal }),
            signal: controller.signal
          });
          window.clearTimeout(timeoutId);
          const data = await res.json();
          // Procesar bloque técnico si existe
          let arr: Message[] = [];
          if (data.message && data.message.trim().length > 0) {
            const tipo = esBloqueYaml(data.message) ? "yaml" : "text";
            arr.push({ from: "ai", text: data.message, type: tipo });
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
          if (err && err.name === 'AbortError') {
            setMessages((msgs: Message[]) => [...msgs, { from: "ai", text: "El servidor está tardando demasiado en responder. Intenta de nuevo más tarde.", type: "text" }]);
          } else {
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
        <div className="flex-1 overflow-y-auto p-6">
        {/* Pantalla de bienvenida cuando no hay mensajes */}
        {messages.length === 0 && (
          <div className="flex-1 flex items-center justify-center min-h-96">
            <div className="text-center space-y-6 max-w-md">
              <div className="text-4xl">🧬</div>
              <h2 className="text-2xl font-bold text-gray-800 dark:text-white">
                Bienvenido a Calyx AI
              </h2>
              <p className="text-gray-600 dark:text-gray-300">
                Asistente de cálculos médicos con IA local
              </p>
              
              {/* Mostrar progreso del backend si está iniciándose */}
              {showBackendProgress && (
                <BackendStartupProgress 
                  onReady={() => setShowBackendProgress(false)}
                  className="max-w-md mx-auto"
                />
              )}
              
              {/* Estado del modelo cuando el backend esté listo */}
              {!showBackendProgress && (
                <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border">
                  <ModelStatusIndicator showDetails={true} className="text-base" />
                </div>
              )}
              
              {/* Mensaje adicional si hay error de conexión (solo cuando no se muestra progreso) */}
              {!showBackendProgress && modelError && (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                  <p className="text-red-700 dark:text-red-300 text-sm">
                    No se puede conectar con el backend. Asegúrate de que el servidor esté ejecutándose en el puerto 8000.
                  </p>
                </div>
              )}
              
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Escribe tu consulta médica para comenzar
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
              <div key={i} className="mb-4 flex justify-start">
                <ConsoleRenderer 
                  title={msg.title} 
                  input={msg.input} 
                  output={msg.output} 
                  onTypingStart={handleTypingStart}
                  onTypingEnd={handleTypingEnd}
                />
              </div>
            );
          } else {
            return (
              <div key={i} className="mb-4 flex justify-start">
                <ConsoleRenderer text={msg.text} />
              </div>
            );
          }
        })}
        <div ref={messagesEndRef} />
      </div>
      
      {/* Indicador de estado del modelo (solo cuando hay mensajes) */}
      {messages.length > 0 && (
        <div className="px-6 pb-2">
          <ModelStatusIndicator className="text-sm opacity-75" />
        </div>
      )}
      
      <div className="p-6 bg-transparent">
        <div className="flex items-center border border-gray-300 dark:border-gray-600 rounded-2xl px-4 py-2 shadow-md bg-white dark:bg-gray-800 transition-colors">
          <input
            ref={inputRef}
            type="text"
            className={`flex-1 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 outline-none border-none text-base py-2 transition-colors ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
            placeholder={
              loading ? "Procesando respuesta..." : 
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
