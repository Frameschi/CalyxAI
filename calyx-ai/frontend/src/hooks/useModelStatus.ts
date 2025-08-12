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
      
      const response = await fetch('http://localhost:8000/model/status', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Error HTTP: ${response.status}`);
      }

      const data: ModelStatus = await response.json();
      setModelStatus(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido';
      setError(errorMessage);
      setModelStatus({
        status: 'error',
        message: `Error al verificar el estado del modelo: ${errorMessage}`,
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
    
    // Verificar estado cada 10 segundos si el modelo está cargando
    const interval = setInterval(() => {
      if (modelStatus?.status === 'loading' || modelStatus?.status === 'not_downloaded') {
        checkModelStatus();
      }
    }, 10000);

    return () => clearInterval(interval);
  }, [checkModelStatus, modelStatus?.status]);

  return {
    modelStatus,
    isLoading,
    error,
    checkModelStatus,
    refetch,
  };
};

export default useModelStatus;
