
import React, { useState } from "react";
import { ConsoleRenderer } from "../components/ConsoleRenderer";
import { esBloqueYaml } from "../utils/formatConsole";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function Chat() {
  interface Message {
    from: "ai" | "user";
    text: string;
    type: "text" | "yaml";
  }

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  // Palabras clave para detectar preguntas sobre alimentos
  const patronesAlimento = [
    /informaci[óo]n completa de ([a-zA-Záéíóúñ ]+)/i,
    /informaci[óo]n de ([a-zA-Záéíóúñ ]+)/i,
    /datos de ([a-zA-Záéíóúñ ]+)/i,
    /aporta ([a-zA-Záéíóúñ ]+)/i,
    /cu[aá]nt[ao]s? (?:calor[ií]as|prote[ií]nas|grasas|fibra|sodio) .* ([a-zA-Záéíóúñ ]+)/i
  ];

  const handleSend = async () => {
    if (input.trim() === "" || loading) return;
    const userMsg = input;
    setMessages([...messages, { from: "user", text: userMsg, type: "text" }]);
    setInput("");
    setLoading(true);
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
            // Adaptar a la estructura real del backend
            let principal = null;
            if (data.filas && typeof data.filas === 'object') {
              principal = data.filas;
            } else if (data.info_completa && Array.isArray(data.info_completa)) {
              principal = data.info_completa;
            }
            let encabezado = `Información de ${alimentoDetectado}`;
            if (principal) {
              respuesta += `${encabezado}:\n`;
              // Si principal es un objeto simple (no array)
              if (principal && typeof principal === 'object' && !Array.isArray(principal)) {
                // Si tiene clave/valor, mostrar solo el valor de "clave" y "valor" de forma amigable
                if (principal.clave && principal.valor) {
                  respuesta += `• ${principal.clave}: ${principal.valor}\n`;
                } else {
                  // Mostrar todos los campos excepto "clave", "valor", "linea"
                  Object.entries(principal).forEach(([k, v]) => {
                    if (!["clave", "valor", "linea"].includes(k)) {
                      respuesta += `• ${k}: ${v}\n`;
                    }
                  });
                }
              } else if (Array.isArray(principal)) {
                // Si es un array, mostrar cada objeto de forma limpia
                principal.forEach((item) => {
                  if (typeof item === 'object') {
                    // Si el objeto tiene "clave" y "valor", mostrar solo eso
                    if (item.clave && item.valor) {
                      respuesta += `• ${item.clave}: ${item.valor}\n`;
                    } else {
                      // Mostrar todos los campos excepto "clave", "valor", "linea"
                      Object.entries(item).forEach(([k, v]) => {
                        if (!["clave", "valor", "linea"].includes(k)) {
                          respuesta += `• ${k}: ${v}\n`;
                        }
                      });
                    }
                    respuesta += '\n';
                  } else {
                    respuesta += `${item}\n`;
                  }
                });
              }
            }
            if (data.sugerencias && Array.isArray(data.sugerencias) && data.sugerencias.length > 0) {
              respuesta += `\nOtras variantes: ${data.sugerencias.join(", ")}`;
            }
            const tipo = esBloqueYaml(respuesta) ? "yaml" : "text";
            setMessages((msgs: Message[]) => [...msgs, { from: "ai", text: respuesta, type: tipo }]);
          }
        } catch (err) {
          setMessages((msgs: Message[]) => [...msgs, { from: "ai", text: "Error de conexión con el backend de alimentos.", type: "text" }]);
        }
        return;
      }

      // Si no es pregunta de alimento, usar IA general
      try {
        // Mantener contexto: enviar historial de mensajes relevantes
        const contexto = messages.slice(-6).map((m: Message) => `${m.from}: ${m.text}`).join('\n');
        const promptFinal = `${contexto}\nuser: ${userMsg}`;
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
          // Si la respuesta está cortada, avisar y sugerir continuar
          let respuesta = data.response || "(Sin respuesta)";
          if (respuesta.endsWith("¿Quieres que continúe la respuesta?")) {
            respuesta = respuesta.replace("¿Quieres que continúe la respuesta?", "[Respuesta incompleta. Escribe 'continuar' para seguir.] ");
          }
          // Explicar limitaciones técnicas de forma clara y útil
          if (/no estoy capacitado para calcular/i.test(respuesta)) {
            respuesta += "\nPuedes usar el bloque técnico para cálculos simples, o consultar fuentes confiables para resultados médicos.";
          }
          // Evitar respuestas genéricas
          if (/porción recomendada|consulta a un experto|aplicaciones dedicadas/i.test(respuesta)) {
            respuesta += "\nSi necesitas datos concretos, por favor especifica cantidad, unidad y contexto.";
          }
          const tipo = esBloqueYaml(respuesta) ? "yaml" : "text";
          setMessages((msgs: Message[]) => [...msgs, { from: "ai", text: respuesta, type: tipo }]);
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
    }
  };

  return (
    <div className="flex flex-col h-screen bg-white">
      <div className="flex-1 overflow-y-auto p-6">
        {messages.map((msg: Message, i: number) => {
          if (msg.from === "user") {
            return (
              <div
                key={i}
                className="mb-4 flex justify-end"
              >
                <div className="bg-gray-100 text-gray-900 px-4 py-2 rounded-2xl max-w-lg shadow border border-gray-300">
                  {msg.text}
                </div>
              </div>
            );
          } else if (msg.type === "yaml") {
            // Renderizar bloque YAML
            const { ConsoleBlockYaml } = require("../components/ConsoleBlockYaml");
            return <ConsoleBlockYaml key={i} input={msg.text} />;
          } else {
            // Renderizar bloque técnico o texto normal
            return (
              <div key={i} className="mb-4 flex justify-start">
                <ConsoleRenderer text={msg.text} />
              </div>
            );
          }
        })}
      </div>
      <div className="p-6 bg-transparent">
        <div className="flex items-center border border-black rounded-2xl px-4 py-2 shadow-md bg-white">
          <input
            type="text"
            className="flex-1 bg-white text-gray-900 placeholder-gray-400 outline-none border-none text-base py-2"
            placeholder="Escribe tu mensaje..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
          />
          <button
            onClick={handleSend}
            className="ml-2 bg-white rounded-full p-0 hover:bg-gray-200 transition flex items-center justify-center border border-black shadow"
            aria-label="Enviar"
            style={{ width: 56, height: 56 }}
          >
            <img
              src={window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? '/send-white.svg' : '/send-black.svg'}
              alt="Enviar"
              className="w-10 h-10"
              style={{ filter: 'drop-shadow(0 0 1px #000)' }}
            />
          </button>
        </div>
      </div>
    </div>
  );
}
