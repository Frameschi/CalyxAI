import { useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function Chat() {
  const [messages, setMessages] = useState([
    { from: "ai", text: "¡Hola! ¿En qué puedo ayudarte hoy?" },
  ]);
  const [input, setInput] = useState("");

  // Palabras clave para detectar preguntas sobre alimentos
  const patronesAlimento = [
    /informaci[óo]n completa de ([a-zA-Záéíóúñ ]+)/i,
    /informaci[óo]n de ([a-zA-Záéíóúñ ]+)/i,
    /datos de ([a-zA-Záéíóúñ ]+)/i,
    /aporta ([a-zA-Záéíóúñ ]+)/i,
    /cu[aá]nt[ao]s? (?:calor[ií]as|prote[ií]nas|grasas|fibra|sodio) .* ([a-zA-Záéíóúñ ]+)/i
  ];

  const handleSend = async () => {
    if (input.trim() === "") return;
    const userMsg = input;
    setMessages([...messages, { from: "user", text: userMsg }]);
    setInput("");

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
        // Si es información completa, pasar el texto completo
        const nombreParam = esCompleta ? `informacion completa de ${alimentoDetectado}` : alimentoDetectado;
        const res = await fetch(`${API_URL}/alimento?nombre=${encodeURIComponent(nombreParam)}`);
        const data = await res.json();
        if (data.error) {
          setMessages(msgs => [...msgs, { from: "ai", text: `No se encontró información para "${alimentoDetectado}".` }]);
        } else {
          let respuesta = `Información de ${alimentoDetectado} (más común):\n`;
          for (const [k, v] of Object.entries(data.alimento_principal)) {
            respuesta += `• ${k}: ${v}\n`;
          }
          if (data.sugerencias && data.sugerencias.length > 0) {
            respuesta += `\nOtras variantes: ${data.sugerencias.join(", ")}`;
          }
          setMessages(msgs => [...msgs, { from: "ai", text: respuesta }]);
        }
      } catch (err) {
        setMessages(msgs => [...msgs, { from: "ai", text: "Error de conexión con el backend de alimentos." }]);
      }
      return;
    }

    // Si no es pregunta de alimento, usar IA general
    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: userMsg })
      });
      const data = await res.json();
      setMessages(msgs => [...msgs, { from: "ai", text: data.response || "(Sin respuesta)" }]);
    } catch (err) {
      setMessages(msgs => [...msgs, { from: "ai", text: "Error de conexión con el backend." }]);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-white">
      <div className="flex-1 overflow-y-auto p-6">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`mb-4 flex ${msg.from === "user" ? "justify-end" : "justify-start"}`}
          >
            {msg.from === "user" ? (
              <div className="bg-gray-100 text-gray-900 px-4 py-2 rounded-2xl max-w-lg shadow border border-gray-300">
                {msg.text}
              </div>
            ) : (
              <div className="text-base text-gray-800 max-w-lg whitespace-pre-line">{msg.text}</div>
            )}
          </div>
        ))}
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
