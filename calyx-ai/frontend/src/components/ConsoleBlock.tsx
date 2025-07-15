// components/ConsoleBlock.tsx
import React from 'react';
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
  // Detecta tablas markdown: filas separadas por \n, columnas por |
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
  // Si no es tabla, mostrar como texto
  return <pre className="text-sm text-white whitespace-pre-wrap">{output}</pre>;
}

export const ConsoleBlock: React.FC<ConsoleBlockProps> = ({ title, input, output }) => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.3 }}
    className={`${typeColors[title] || 'bg-gray-900'} text-white rounded-xl p-4 mb-4 shadow-md`}
  >
    <div className="flex items-center mb-2">
      <span className="text-lg mr-2">{typeIcons[title] || '💬'}</span>
      <span className="text-xs uppercase text-gray-300">{title}</span>
    </div>
    <pre className="text-sm text-green-300 whitespace-pre-wrap">{input}</pre>
    <hr className="my-2 border-gray-600" />
    {renderOutput(output)}
  </motion.div>
);