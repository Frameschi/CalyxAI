import { useState, useEffect, useCallback } from 'react';

interface ModelStatus {
  status: 'checking' | 'not_downloaded' | 'loading' | 'ready' | 'error';
  message: string;
  model_ready: boolean;
  model_name: string;
  device?: string;
  is_downloaded?: boolean;
  cache_size_mb?: number;
  cache_path?: string;
}

interface UseModelStatusReturn {
  modelStatus: ModelStatus | null;
  isLoading: boolean;
  error: string | null;
  checkModelStatus: () => Promise<void>;
  refetch: () => void;
}

export const useModelStatus = (): UseModelStatusReturn => {
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const checkModelStatus = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Primero verificar si el backend está disponible con ping
      try {
        const pingResponse = await fetch('http://localhost:8000/ping', {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
          timeout: 3000  // Timeout de 3 segundos
        } as RequestInit);

        if (!pingResponse.ok) {
          throw new Error('Backend no disponible');
        }
      } catch (pingError) {
        // Si el ping falla, el backend no está disponible
        setError('No se puede conectar con el backend');
        setModelStatus({
          status: 'error',
          message: 'No se puede conectar con el backend. Asegúrate de que el servidor esté ejecutándose en el puerto 8000.',
          model_ready: false,
          model_name: 'microsoft/phi-3-mini-4k-instruct'
        });
        return;
      }
      
      // Si el ping funciona, verificar el estado del modelo
      const response = await fetch('http://localhost:8000/model/status', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 10000  // Timeout más largo para status del modelo
      } as RequestInit);

      if (!response.ok) {
        throw new Error(`Error HTTP: ${response.status}`);
      }

      const data: ModelStatus = await response.json();
      setModelStatus(data);
      
      // Limpiar el error si el modelo está ready
      if (data.status === 'ready') {
        setError(null);
      }
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido';
      
      // Solo mostrar error si no es por timeout o conexión
      if (!errorMessage.includes('fetch') && !errorMessage.includes('Failed to fetch')) {
        setError(errorMessage);
      } else {
        setError('No se puede conectar con el backend');
      }
      
      setModelStatus({
        status: 'error',
        message: errorMessage.includes('fetch') || errorMessage.includes('Failed to fetch') 
          ? 'No se puede conectar con el backend. Asegúrate de que el servidor esté ejecutándose en el puerto 8000.'
          : `Error al verificar el estado del modelo: ${errorMessage}`,
        model_ready: false,
        model_name: 'microsoft/phi-3-mini-4k-instruct'
      });
    } finally {
      setIsLoading(false);
    }
  }, []);

  const refetch = useCallback(() => {
    checkModelStatus();
  }, [checkModelStatus]);

  useEffect(() => {
    checkModelStatus();
    
    // Función para determinar el intervalo basado en el estado actual
    const getInterval = () => {
      if (modelStatus?.status === 'ready') {
        return 60000; // Cada 60 segundos si está listo (mucho menos frecuente)
      } else if (modelStatus?.status === 'loading') {
        return 10000; // Cada 10 segundos si está cargando
      } else if (modelStatus?.status === 'error' || error) {
        return 15000; // Cada 15 segundos si hay error
      } else if (modelStatus?.status === 'not_downloaded') {
        return 30000; // Cada 30 segundos si no está descargado
      }
      return 20000; // Cada 20 segundos por defecto (más conservador)
    };
    
    const interval = setInterval(() => {
      checkModelStatus();
    }, getInterval());

    return () => clearInterval(interval);
  }, [checkModelStatus, modelStatus?.status, error]); // Recrear intervalo cuando cambie el estado

  return {
    modelStatus,
    isLoading,
    error,
    checkModelStatus,
    refetch,
  };
};

export default useModelStatus;
