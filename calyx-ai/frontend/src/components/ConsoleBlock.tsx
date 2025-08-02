// components/ConsoleBlock.tsx
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

interface ConsoleBlockProps {
  title: string;
  input: string;
  output: string;
}

const typeIcons: Record<string, string> = {
  'Python': '🐍',
  'Cálculo': '🧮',
  'Nutrición': '🥗',
  'Consola': '💬',
  'Error': '⚠️',
};

// Componente de terminal con cursor único
const TerminalTypewriter: React.FC<{ content: string }> = ({ content }) => {
  const [displayedText, setDisplayedText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showCursor, setShowCursor] = useState(true);

  useEffect(() => {
    if (currentIndex < content.length) {
      const timer = setTimeout(() => {
        setDisplayedText(content.slice(0, currentIndex + 1));
        setCurrentIndex(currentIndex + 1);
      }, 50); // Velocidad de typing
      return () => clearTimeout(timer);
    }
  }, [currentIndex, content]);

  useEffect(() => {
    const cursorInterval = setInterval(() => {
      setShowCursor(prev => !prev);
    }, 500); // Parpadeo del cursor
    return () => clearInterval(cursorInterval);
  }, []);

  return (
    <div className="text-sm text-white font-mono whitespace-pre-wrap mb-2">
      {displayedText}
      <span className={`${showCursor ? 'opacity-100' : 'opacity-0'} transition-opacity`}>
        █
      </span>
    </div>
  );
};

export const ConsoleBlock: React.FC<ConsoleBlockProps> = ({ title, input, output }) => {
  // El contenido principal será input si existe, si no output
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`bg-[#23272e] text-white rounded-xl p-0 mb-4 shadow-md border border-gray-800 font-mono`}
      style={{
        minWidth: '340px',
        width: '45%',
        minHeight: '320px',
        maxWidth: '600px',
        overflowY: 'auto',
        overflowX: 'auto',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'flex-start',
      }}
    >
      <div className="flex items-center px-4 py-3 bg-[#23272e] border-b border-gray-800 rounded-t-xl">
        <span className="text-lg mr-2">{typeIcons['Cálculo'] || '💬'}</span>
        <span className="text-xs uppercase text-gray-300 font-semibold tracking-wide">Cálculo</span>
      </div>
      <div className="px-4 pt-3 pb-2">
        {(() => {
          const content = (input && input.trim().length > 0 ? input.trim() + '\n' : '') + (output && output.trim().length > 0 ? output.trim() : '');
          return <TerminalTypewriter content={content} />;
        })()}
      </div>
    </motion.div>
  );
};
