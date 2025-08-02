import React from 'react';
import { ConsoleBlock } from './ConsoleBlock';

interface Props {
  text?: string;
  title?: string;
  input?: string;
  output?: string;
}

export const ConsoleRenderer: React.FC<Props> = ({ text, title, input, output }) => {
  // Si recibe props de bloque técnico, renderiza ConsoleBlock
  if (title || input || output) {
    return <ConsoleBlock title={title || ''} input={input || ''} output={output || ''} />;
  }
  // Si no tiene formato especial, renderiza como chat
  return <div className="bg-white text-black p-3 rounded-xl shadow mb-4">{text}</div>;
};
