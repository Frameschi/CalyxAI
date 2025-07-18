import { useState } from "react";

// Carga el JSON de fórmulas (puedes importar o fetch si lo prefieres)

import formulasData from "../data/data_formulas.json";
type FormulasData = typeof formulasData;
type FormulaKey = keyof FormulasData;
type Formula = FormulasData[FormulaKey];

type ParamValue = string | number;

interface FormulaResult {
  nombre: string;
  resultado: number;
  interpretacion?: string;
}

/**
 * Hook para resolver una fórmula, detectando dependencias automáticamente.
 * Si un parámetro coincide con el nombre de otra fórmula, solicita/calcule primero esa fórmula.
 */
export function useFormulaResolver() {
  const [resultados, setResultados] = useState<Record<string, FormulaResult>>({});

  // Resuelve una fórmula por nombre, pidiendo los parámetros necesarios
  async function resolverFormula(nombre: string, valores: Record<string, ParamValue>): Promise<FormulaResult> {
    const formula: Formula | undefined = formulasData[nombre as FormulaKey];
    if (!formula) throw new Error(`Fórmula no encontrada: ${nombre}`);

    // Detectar dependencias y parámetros faltantes
    const valoresCompletos: Record<string, ParamValue> = { ...valores };
    const faltantes: string[] = [];
    for (const param of formula.parametros) {
      if (valoresCompletos[param.nombre] === undefined) {
        // ¿Existe una fórmula con ese nombre?
        if (formulasData[param.nombre as FormulaKey]) {
          // Resolver la fórmula dependiente recursivamente
          const resDep = await resolverFormula(param.nombre, valores);
          valoresCompletos[param.nombre] = resDep.resultado;
        } else {
          faltantes.push(param.nombre);
        }
      }
    }
    if (faltantes.length > 0) {
      throw new Error(`Faltan los siguientes datos para calcular ${nombre}: ${faltantes.join(", ")}`);
    }

    // Calcular el resultado (aquí debes implementar la lógica real de cada fórmula)
    // Ejemplo: solo para IMC
    let resultado = 0;
    if (nombre === "imc") {
      resultado = Number(valoresCompletos.peso) / Math.pow(Number(valoresCompletos.altura), 2);
    } else if (nombre === "get") {
      resultado = Number(valoresCompletos.tmb) * Number(valoresCompletos.factor_actividad);
    } else {
      // Aquí puedes agregar más fórmulas o usar una función de cálculo genérica
      throw new Error(`Cálculo no implementado para: ${nombre}`);
    }

    // Buscar interpretación
    let interpretacion = undefined;
    if (formula.interpretacion) {
      for (const rango of formula.interpretacion) {
        if (resultado >= rango.min && resultado < rango.max) {
          interpretacion = rango.texto;
          break;
        }
      }
    }

    const res: FormulaResult = { nombre, resultado, interpretacion };
    setResultados(prev => ({ ...prev, [nombre]: res }));
    return res;
  }

  return { resultados, resolverFormula };
}
