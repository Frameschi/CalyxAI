import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
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

  // Función para detectar si el texto contiene sintaxis Markdown
  const hasMarkdownSyntax = (text: string): boolean => {
    // Detectar tablas Markdown (| para columnas)
    if (text.includes('|') && text.includes('\n|')) return true;
    // Detectar negritas (**texto**)
    if (/\*\*.*\*\*/.test(text)) return true;
    // Detectar cursivas (*texto*)
    if (/(?<!\*)\*[^*]+\*(?!\*)/.test(text)) return true;
    // Detectar listas (- item)
    if (/^\s*-\s/m.test(text)) return true;
    // Detectar headers (# texto)
    if (/^#{1,6}\s/m.test(text)) return true;
    // Detectar código (`codigo`)
    if (/`[^`]+`/.test(text)) return true;
    return false;
  };

  // Si no tiene formato especial, renderiza como chat normal o con Markdown
  if (text && hasMarkdownSyntax(text)) {
    return (
      <div className="bg-white dark:bg-gray-800 text-black dark:text-white p-4 rounded-xl shadow mb-4 border border-gray-200 dark:border-gray-700 transition-colors">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            table: ({ children }) => (
              <div className="overflow-x-auto">
                <table className="min-w-full border-collapse border border-gray-300 dark:border-gray-600 text-sm">
                  {children}
                </table>
              </div>
            ),
            thead: ({ children }) => (
              <thead className="bg-gray-50 dark:bg-gray-700">
                {children}
              </thead>
            ),
            tbody: ({ children }) => (
              <tbody className="divide-y divide-gray-200 dark:divide-gray-600">
                {children}
              </tbody>
            ),
            tr: ({ children }) => (
              <tr className="hover:bg-gray-50 dark:hover:bg-gray-700">
                {children}
              </tr>
            ),
            th: ({ children }) => (
              <th className="border border-gray-300 dark:border-gray-600 px-3 py-2 text-left font-semibold text-gray-900 dark:text-white">
                {children}
              </th>
            ),
            td: ({ children }) => (
              <td className="border border-gray-300 dark:border-gray-600 px-3 py-2 text-gray-700 dark:text-gray-300">
                {children}
              </td>
            ),
            strong: ({ children }) => (
              <strong className="font-semibold text-gray-900 dark:text-white">
                {children}
              </strong>
            ),
            em: ({ children }) => (
              <em className="italic text-gray-700 dark:text-gray-300">
                {children}
              </em>
            ),
            ul: ({ children }) => (
              <ul className="list-disc list-inside space-y-1 my-2">
                {children}
              </ul>
            ),
            ol: ({ children }) => (
              <ol className="list-decimal list-inside space-y-1 my-2">
                {children}
              </ol>
            ),
            li: ({ children }) => (
              <li className="text-gray-700 dark:text-gray-300">
                {children}
              </li>
            ),
            p: ({ children }) => (
              <p className="mb-2 text-gray-700 dark:text-gray-300 leading-relaxed">
                {children}
              </p>
            ),
            h1: ({ children }) => (
              <h1 className="text-xl font-bold text-gray-900 dark:text-white mb-3 mt-4 first:mt-0">
                {children}
              </h1>
            ),
            h2: ({ children }) => (
              <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-2 mt-3">
                {children}
              </h2>
            ),
            h3: ({ children }) => (
              <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-2 mt-3">
                {children}
              </h3>
            ),
            code: ({ children }) => (
              <code className="bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded text-sm font-mono text-gray-800 dark:text-gray-200">
                {children}
              </code>
            ),
            blockquote: ({ children }) => (
              <blockquote className="border-l-4 border-blue-500 pl-4 italic text-gray-600 dark:text-gray-400 my-2">
                {children}
              </blockquote>
            ),
          }}
        >
          {text}
        </ReactMarkdown>
      </div>
    );
  }

  // Texto plano normal
  return <div className="bg-white dark:bg-gray-800 text-black dark:text-white p-3 rounded-xl shadow mb-4 border border-gray-200 dark:border-gray-700 transition-colors">{text}</div>;
};
