// Test component for Markdown rendering
import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const testMarkdown = `
# Información Nutricional - Arroz Integral Cocido

El arroz integral cocido es una excelente opción alimenticia rica en nutrientes.

| Componente | Valor por 100g |
|------------|----------------|
| Energía (kcal) | 342 |
| Proteínas (g) | 2.7 |
| Grasas Total (g) | 0.4 |
| Carbohidratos (g) | 76.2 |
| Fibra (g) | 2.7 |
| Hierro (mg) | 1.5 |
| Calcio (mg) | 21 |

**Fuente:** Datos obtenidos de la base de datos SMAE
`;

export const MarkdownTest: React.FC = () => {
  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Test de Markdown</h2>
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
          h1: ({ children }) => (
            <h1 className="text-xl font-bold text-gray-900 dark:text-white mb-3">
              {children}
            </h1>
          ),
          p: ({ children }) => (
            <p className="mb-2 text-gray-700 dark:text-gray-300 leading-relaxed">
              {children}
            </p>
          ),
        }}
      >
        {testMarkdown}
      </ReactMarkdown>
    </div>
  );
};