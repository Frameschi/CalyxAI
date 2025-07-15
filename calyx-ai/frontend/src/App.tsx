import React, { useEffect, useRef, useState } from 'react';
import { ConsoleRenderer } from './components/ConsoleRenderer';

interface BlockData {
  title: string;
  input: string;
  output: string;
}

const App: React.FC = () => {
  const [blocks, setBlocks] = useState<BlockData[]>([]);
  const [userInput, setUserInput] = useState('');
  const [loading, setLoading] = useState(false);
  const blocksEndRef = useRef<HTMLDivElement>(null);

  // Scroll automático al agregar bloque
  useEffect(() => {
    if (blocksEndRef.current) {
      blocksEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [blocks]);

  // Simulación de tipo de bloque según el input
  function getBlockTitle(input: string): string {
    if (/imc|peso|altura/i.test(input)) return 'Cálculo';
    if (/python|código|script/i.test(input)) return 'Python';
    if (/caloría|nutrición|proteína|fibra/i.test(input)) return 'Nutrición';
    return 'Consola';
  }

  const handleSend = async () => {
    if (!userInput.trim()) return;
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: userInput })
      });
      const data = await res.json();
      const output = data.response || data.error || 'Sin respuesta';
      setBlocks(prev => [
        ...prev,
        {
          title: getBlockTitle(userInput),
          input: userInput,
          output: output
        }
      ]);
      setUserInput('');
    } catch (e) {
      setBlocks(prev => [
        ...prev,
        {
          title: 'Error',
          input: userInput,
          output: 'No se pudo conectar al backend.'
        }
      ]);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-950 p-6 flex flex-col items-center">
      <h1 className="text-2xl font-bold text-white mb-6">Calyx AI - Consola Interactiva</h1>
      <div className="w-full max-w-xl mb-4">
        <textarea
          className="w-full p-3 rounded-lg bg-gray-800 text-white mb-2 focus:outline-none"
          rows={2}
          placeholder="Escribe tu consulta, cálculo o fórmula..."
          value={userInput}
          onChange={e => setUserInput(e.target.value)}
          disabled={loading}
        />
        <button
          className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg w-full font-semibold"
          onClick={handleSend}
          disabled={loading}
        >
          {loading ? 'Procesando...' : 'Enviar'}
        </button>
      </div>
      <div className="w-full max-w-xl overflow-y-auto" style={{ maxHeight: '70vh' }}>
        {blocks.map((block, idx) => (
          <ConsoleRenderer key={idx} text={block.output} />
        ))}
        <div ref={blocksEndRef} />
      </div>
    </div>
  );
};

export default App;
