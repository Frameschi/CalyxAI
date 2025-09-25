
export function esBloqueYaml(texto: string): boolean {
  // NO detectar como YAML respuestas que contienen tablas Markdown (con |)
  if (texto.includes('|') && texto.includes('\n|')) {
    return false;
  }

  // NO detectar como YAML respuestas nutricionales (contienen palabras clave)
  const palabrasNutricion = ['aporte nutricional', 'información nutricional', 'valor nutricional', 'calorías', 'proteínas', 'grasas', 'carbohidratos', 'fibra', 'sodio', 'hierro', 'calcio'];
  if (palabrasNutricion.some(palabra => texto.toLowerCase().includes(palabra))) {
    return false;
  }

  // Detecta si tiene header tipo # y líneas clave: valor (solo para bloques técnicos reales)
  return /(^|\n)#\s*.+/.test(texto) && /:\s*.+/.test(texto);
}

export function esRespuestaDeConsola(texto: string): boolean {
  return texto.includes('Paso 1:') || texto.includes('Resultado:') || texto.includes('[ CÁLCULO') || texto.startsWith('[ PYTHON ]') || esBloqueYaml(texto);
}

export function formatConsole(text: string) {
  // Detecta si es bloque técnico o YAML
  if (esBloqueYaml(text)) {
    return { isConsole: true, isYaml: true, input: text };
  }
  const isConsole = text.includes('Paso 1:') || text.includes('Resultado:') || text.includes('[ CÁLCULO') || text.startsWith('[ PYTHON ]');
  if (!isConsole) return { isConsole: false };
  const lines = text.split('\n');
  const title = lines[0].replace('[', '').replace(']', '').trim();
  const input = lines.slice(1, lines.length - 1).join('\n');
  const output = lines[lines.length - 1];
  return { isConsole: true, isYaml: false, title, input, output };
}
