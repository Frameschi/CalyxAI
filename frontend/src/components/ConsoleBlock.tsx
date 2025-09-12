// components/ConsoleBlock.tsx
import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

interface ConsoleBlockProps {
  title: string;
  input: string;
  output: string;
  onTypingStart?: () => void;
  onTypingEnd?: () => void;
}

const typeIcons: Record<string, string> = {
  'Python': '🐍',
  'Cálculo': '🧮',
  'Nutrición': '🥗',
  'Consola': '💬',
  'Error': '⚠️',
};

// Componente de terminal con cursor único
const TerminalTypewriter: React.FC<{ content: string; onTypingStart?: () => void; onTypingEnd?: () => void }> = ({ content, onTypingStart, onTypingEnd }) => {
  const [displayedText, setDisplayedText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showCursor, setShowCursor] = useState(true);
  const [hasStarted, setHasStarted] = useState(false);
  const [isPageVisible, setIsPageVisible] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);
  const typingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const cursorTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Detectar visibilidad de la página (para Electron y navegadores)
  useEffect(() => {
    const handleVisibilityChange = () => {
      setIsPageVisible(!document.hidden);
    };
    
    // Para Electron, también escuchar eventos de focus/blur de la ventana
    const handleFocus = () => setIsPageVisible(true);
    const handleBlur = () => setIsPageVisible(false);
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('focus', handleFocus);
    window.addEventListener('blur', handleBlur);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleFocus);
      window.removeEventListener('blur', handleBlur);
    };
  }, []);

  useEffect(() => {
    if (!hasStarted && content.length > 0) {
      setHasStarted(true);
      onTypingStart?.();
    }
  }, [content, hasStarted, onTypingStart]);

  useEffect(() => {
    // Limpiar timer anterior si existe
    if (typingTimerRef.current) {
      clearTimeout(typingTimerRef.current);
    }
    
    if (currentIndex < content.length) {
      // Usar velocidad normal siempre (25ms) - sin importar si está minimizado
      const typingSpeed = 25;
      
      typingTimerRef.current = setTimeout(() => {
        setDisplayedText(content.slice(0, currentIndex + 1));
        setCurrentIndex(currentIndex + 1);
        
        // Scroll automático durante la escritura (solo si es visible)
        if (isPageVisible && containerRef.current) {
          containerRef.current.scrollIntoView({ behavior: "smooth", block: "end" });
        }
      }, typingSpeed);
      
    } else if (currentIndex >= content.length && hasStarted && content.length > 0) {
      // Typing terminado - ejecutar callback
      typingTimerRef.current = setTimeout(() => {
        onTypingEnd?.();
      }, 100);
    }
    
    return () => {
      if (typingTimerRef.current) {
        clearTimeout(typingTimerRef.current);
      }
    };
  }, [currentIndex, content, hasStarted, onTypingEnd]); // Removido isPageVisible de las dependencias

  useEffect(() => {
    // Limpiar timer anterior si existe
    if (cursorTimerRef.current) {
      clearInterval(cursorTimerRef.current);
    }
    
    // Parpadeo del cursor - pausar cuando no es visible para ahorrar recursos
    if (isPageVisible) {
      cursorTimerRef.current = setInterval(() => {
        setShowCursor(prev => !prev);
      }, 250);
    } else {
      // Mantener cursor visible cuando está minimizado
      setShowCursor(true);
    }
    
    return () => {
      if (cursorTimerRef.current) {
        clearInterval(cursorTimerRef.current);
      }
    };
  }, [isPageVisible]);

  return (
    <div ref={containerRef} className="text-sm text-white font-mono whitespace-pre-wrap mb-2">
      {displayedText}
      <span className={`${showCursor ? 'opacity-100' : 'opacity-0'} transition-opacity`}>
        █
      </span>
    </div>
  );
};

export const ConsoleBlock: React.FC<ConsoleBlockProps> = ({ title, input, output, onTypingStart, onTypingEnd }) => {
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
          return <TerminalTypewriter content={content} onTypingStart={onTypingStart} onTypingEnd={onTypingEnd} />;
        })()}
      </div>
    </motion.div>
  );
};
