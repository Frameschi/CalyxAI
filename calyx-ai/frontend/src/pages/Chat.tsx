
import React, { useState } from "react";
import { ConsoleRenderer } from "../components/ConsoleRenderer";
import { ConsoleBlockYaml } from "../components/ConsoleBlockYaml";
import { esBloqueYaml } from "../utils/formatConsole";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function Chat() {
  interface Message {
    from: "ai" | "user";
    text: string;
    type: "text" | "yaml" | "console";
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
          // Siempre mostrar la respuesta completa, sin preguntar por continuar
          let respuesta = data.response || "(Sin respuesta)";
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
