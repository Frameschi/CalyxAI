export function esRespuestaDeConsola(texto: string): boolean {
  return texto.includes('Paso 1:') || texto.includes('Resultado:') || texto.includes('[ CÁLCULO') || texto.startsWith('[ PYTHON ]');
}
