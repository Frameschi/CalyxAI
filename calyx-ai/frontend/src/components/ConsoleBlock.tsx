// components/ConsoleBlock.tsx
import React, { useState } from 'react';
import Typewriter from 'react-typewriter-effect';
import { motion } from 'framer-motion';

interface ConsoleBlockProps {
  title: string;
  input: string;
  output: string;
}

const typeColors: Record<string, string> = {
  'Python': 'bg-blue-900',
  'Cálculo': 'bg-purple-900',
  'Nutrición': 'bg-green-900',
  'Consola': 'bg-gray-900',
  'Error': 'bg-red-900',
};

const typeIcons: Record<string, string> = {
  'Python': '🐍',
  'Cálculo': '🧮',
  'Nutrición': '🥗',
  'Consola': '💬',
  'Error': '⚠️',
};

// Detectar si el output es una tabla (formato markdown simple)
function renderOutput(output: string) {
  // Detecta tablas tipo markdown
  if (/^\s*\|(.+)\|\s*\n/.test(output)) {
    const rows = output.trim().split('\n').filter(r => r.includes('|'));
    const headers = rows[0].split('|').map(h => h.trim()).filter(Boolean);
    const bodyRows = rows.slice(1).map(row => row.split('|').map(c => c.trim()).filter(Boolean));
    return (
      <table className="w-full text-sm text-white border border-gray-700 rounded-lg overflow-hidden mb-2">
        <thead className="bg-gray-800">
          <tr>
            {headers.map((h, idx) => (
              <th key={idx} className="px-2 py-1 border-r border-gray-700 last:border-r-0">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {bodyRows.map((cols, i) => (
            <tr key={i} className="border-t border-gray-700">
              {cols.map((c, j) => (
                <td key={j} className="px-2 py-1 border-r border-gray-700 last:border-r-0">{c}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    );
  }

  // Mostrar línea por línea con animación
  const lines = output.trim().split('\n');
  return (
    <div className="text-sm text-white whitespace-pre-wrap font-mono space-y-1">
      {lines.map((line, index) => (
        <Typewriter
          key={index}
          text={line}
          typeSpeed={15}
          cursorColor="#fff"
          startDelay={index * 300}
        />
      ))}
    </div>
  );
}

export const ConsoleBlock: React.FC<ConsoleBlockProps> = ({ title, input, output }) => {
  const [copied, setCopied] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editValue, setEditValue] = useState(input);

  const handleCopy = () => {
    navigator.clipboard.writeText(editing ? editValue : input + '\n' + output);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  };

  const handleEdit = () => {
    setEditing(!editing);
    setEditValue(input);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`bg-[#23272e] text-white rounded-xl p-0 mb-4 shadow-md border border-gray-800 font-mono`}
      style={{ overflow: 'hidden' }}
    >
      <div className="flex items-center justify-between px-4 py-3 bg-[#23272e] border-b border-gray-800 rounded-t-xl">
        <div className="flex items-center gap-2">
          <span className="text-lg">{typeIcons[title] || '💬'}</span>
          <span className="text-xs uppercase text-gray-300 font-semibold tracking-wide">{title || 'Bloque Técnico'}</span>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleCopy}
            className="px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded border border-gray-600 text-gray-200 transition"
            title="Copiar bloque"
          >
            {copied ? 'Copiado!' : 'Copiar'}
          </button>
          <button
            onClick={handleEdit}
            className={`px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded border border-gray-600 text-gray-200 transition ${editing ? 'font-bold' : ''}`}
            title="Editar entrada"
          >
            {editing ? 'Cancelar' : 'Editar'}
          </button>
        </div>
      </div>
      <div className="px-4 pt-3 pb-2">
        {editing ? (
          <textarea
            className="w-full bg-gray-900 text-green-300 text-sm font-mono rounded p-2 border border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-600 resize-vertical"
            value={editValue}
            onChange={e => setEditValue(e.target.value)}
            rows={Math.max(2, editValue.split('\n').length)}
          />
        ) : (
          <pre className="text-sm text-green-300 font-mono whitespace-pre-wrap mb-2">{input}</pre>
        )}
        <hr className="my-2 border-gray-700" />
        {renderOutput(output)}
      </div>
    </motion.div>
  );
};
