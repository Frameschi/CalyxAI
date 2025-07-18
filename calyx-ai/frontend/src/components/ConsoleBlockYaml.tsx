import React, { useState } from "react";

interface ConsoleBlockYamlProps {
  input: string;
}

function parseYamlBlock(input: string) {
  // Extrae el header y los pares clave:valor
  const lines = input.split("\n").map(l => l.trim()).filter(Boolean);
  let header = "";
  let pairs: Array<{ key: string; value: string }> = [];
  for (const line of lines) {
    if (line.startsWith("#")) {
      header = line.replace(/^#\s*/, "");
    } else if (line.includes(":")) {
      const [key, ...rest] = line.split(":");
      pairs.push({ key: key.trim(), value: rest.join(":").trim() });
    }
  }
  return { header, pairs };
}

export const ConsoleBlockYaml: React.FC<ConsoleBlockYamlProps> = ({ input }) => {
  const [copied, setCopied] = useState(false);
  const { header, pairs } = parseYamlBlock(input);

  const handleCopy = () => {
    navigator.clipboard.writeText(input);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  };

  return (
    <div className="bg-[#23272e] text-white rounded-xl mb-4 shadow-md border border-gray-800 font-mono overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 bg-[#23272e] border-b border-gray-800 rounded-t-xl">
        <span className="text-xs uppercase text-blue-300 font-semibold tracking-wide">{header || "Bloque YAML"}</span>
        <button
          onClick={handleCopy}
          className="px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded border border-gray-600 text-gray-200 transition"
          title="Copiar bloque"
        >
          {copied ? "Copiado!" : "Copiar"}
        </button>
      </div>
      <div className="px-4 pt-3 pb-2">
        <pre className="text-sm text-yellow-200 font-mono whitespace-pre-wrap mb-2">{input}</pre>
        {pairs.length > 0 && (
          <table className="w-full text-sm text-white border border-gray-700 rounded-lg overflow-hidden mt-2">
            <tbody>
              {pairs.map((p, i) => (
                <tr key={i} className="border-t border-gray-700">
                  <td className="px-2 py-1 border-r border-gray-700 last:border-r-0 text-blue-200 font-semibold">{p.key}</td>
                  <td className="px-2 py-1">{p.value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
