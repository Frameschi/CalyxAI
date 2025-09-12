import React, { useState } from "react";

interface ConsoleBlockYamlProps {
  input: string;
}

function parseYamlBlock(input: string) {
  try {
    const lines = input.split("\n").map(l => l.trim()).filter(Boolean);
    let header = "";
    let pairs: Array<{ key: string; value: string }> = [];
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      if (i === 0 && (line.startsWith("#") || /^[A-ZÁÉÍÓÚa-záéíóúüñ ]+:$/.test(line))) {
        header = line.replace(/^#\s*/, "").replace(/:$/, "");
      } else if (line.includes(":")) {
        const [key, ...rest] = line.split(":");
        if (typeof key === 'string' && rest.length > 0) {
          pairs.push({ key: key.trim(), value: rest.join(":").trim() });
        }
      }
    }
    return { header, pairs };
  } catch (e) {
    return { header: "Error de parseo", pairs: [] };
  }
}

export const ConsoleBlockYaml: React.FC<ConsoleBlockYamlProps> = ({ input }) => {
  const [copied, setCopied] = useState(false);
  const [showPre, setShowPre] = useState(false);
  let header = "";
  let pairs: Array<{ key: string; value: string }> = [];
  let parseError = false;
  try {
    const parsed = parseYamlBlock(input);
    header = parsed.header;
    pairs = parsed.pairs;
  } catch (e) {
    parseError = true;
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(input);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  };

  return (
    <div className="bg-[#23272e] text-white rounded-xl mb-4 shadow-md border border-gray-800 font-mono overflow-hidden ml-0" style={{ maxWidth: '45vw', minWidth: '320px', width: '100%' }}>
      <div className="flex items-center justify-between px-4 py-3 bg-[#23272e] border-b border-gray-800 rounded-t-xl">
        <span className="text-xs uppercase text-blue-300 font-semibold tracking-wide">{header || "Bloque YAML"}</span>
        <div className="flex gap-2">
          <button
            onClick={() => setShowPre(!showPre)}
            className="px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded border border-gray-600 text-gray-200 transition"
            title={showPre ? "Ver como tabla" : "Ver como texto"}
          >
            {showPre ? "Tabla" : "Texto"}
          </button>
          <button
            onClick={handleCopy}
            className="px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded border border-gray-600 text-gray-200 transition"
            title="Copiar bloque"
          >
            {copied ? "Copiado!" : "Copiar"}
          </button>
        </div>
      </div>
      <div className="px-4 pt-3 pb-2">
        {parseError ? (
          <div className="text-red-400 font-bold">Error al procesar el bloque YAML. Revisa el formato de los datos.</div>
        ) : showPre ? (
          <pre className="text-sm text-yellow-200 font-mono whitespace-pre-wrap mb-2">
            {input.split('\n').filter(line => !/^id\s*:/i.test(line)).join('\n')}
          </pre>
        ) : (
          pairs.length > 0 && (
            <table className="w-full text-sm text-white border border-gray-700 rounded-lg overflow-hidden mt-2">
              <tbody>
                {pairs.filter(p => p.key.toLowerCase() !== 'id').map((p, i) => {
                  // Capitalizar la primera letra y mantener el resto igual
                  const keyCap = p.key.charAt(0).toUpperCase() + p.key.slice(1);
                  return (
                    <tr key={i} className="border-t border-gray-700">
                      <td className="px-2 py-1 border-r border-gray-700 last:border-r-0 text-blue-200 font-semibold">{keyCap}</td>
                      <td className="px-2 py-1">{p.value}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )
        )}
      </div>
    </div>
  );
};
