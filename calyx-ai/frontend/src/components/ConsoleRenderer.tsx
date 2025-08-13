import React from 'react';
import { ConsoleBlock } from './ConsoleBlock';

interface Props {
  text?: string;
  title?: string;
  input?: string;
  output?: string;
  onTypingStart?: () => void;
  onTypingEnd?: () => void;
}

export const ConsoleRenderer: React.FC<Props> = ({ text, title, input, output, onTypingStart, onTypingEnd }) => {
  // Si recibe props de bloque técnico, renderiza ConsoleBlock
  if (title || input || output) {
    return <ConsoleBlock title={title || ''} input={input || ''} output={output || ''} onTypingStart={onTypingStart} onTypingEnd={onTypingEnd} />;
  }
  // Si no tiene formato especial, renderiza como chat
  return <div className="bg-white dark:bg-gray-800 text-black dark:text-white p-3 rounded-xl shadow mb-4 border border-gray-200 dark:border-gray-700 transition-colors">{text}</div>;
};
