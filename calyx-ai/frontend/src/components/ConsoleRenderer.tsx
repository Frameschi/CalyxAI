import React from 'react';
import { ConsoleBlock } from './ConsoleBlock';

interface Props {
  text: string;
}

export const ConsoleRenderer: React.FC<Props> = ({ text }) => {
  // Detecta formato de consola por heurística
  if (text.includes('[ CÁLCULO') || text.startsWith('[ PYTHON ]') || text.includes('Paso 1:') || text.includes('Resultado:')) {
    const lines = text.split('\n');
    const title = lines[0].replace('[', '').replace(']', '').trim();
    const input = lines.slice(1, lines.length - 1).join('\n');
    const output = lines[lines.length - 1];
    return <ConsoleBlock title={title} input={input} output={output} />;
  }
  // Si no tiene formato especial, renderiza como chat
  return <div className="bg-white text-black p-3 rounded-xl shadow mb-4">{text}</div>;
};
