import { useState } from "react";

export default function Chat() {
  const [prompt, setPrompt] = useState("");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);

  const sendPrompt = async () => {
    setLoading(true);
    setResponse("");
    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      const data = await res.json();
      setResponse(data.response || data.error || "Sin respuesta");
    } catch (err) {
      setResponse("Error de conexión con el backend");
    }
    setLoading(false);
  };

  return (
    <div className="flex flex-col h-screen">
      <header className="bg-blue-600 text-white p-4">Calyx AI Chat</header>
      <main className="flex-1 p-4 overflow-auto">
        <div className="mb-4">
          <input
            type="text"
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            placeholder="Escribe tu pregunta..."
            className="border p-2 rounded w-2/3"
          />
          <button
            onClick={sendPrompt}
            className="bg-blue-600 text-white px-4 py-2 rounded ml-2"
            disabled={loading || !prompt}
          >
            {loading ? "Enviando..." : "Enviar"}
          </button>
        </div>
        <div className="bg-gray-100 p-4 rounded min-h-[100px]">
          {response}
        </div>
      </main>
    </div>
  );
}
