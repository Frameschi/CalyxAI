import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';

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

interface ModelStatusContextType {
  modelStatus: ModelStatus | null;
  isLoading: boolean;
  error: string | null;
  checkModelStatus: () => Promise<void>;
  refetch: () => void;
}

const ModelStatusContext = createContext<ModelStatusContextType | null>(null);

export const useModelStatus = (): ModelStatusContextType => {
  const context = useContext(ModelStatusContext);
  if (!context) {
    throw new Error('useModelStatus debe ser usado dentro de un ModelStatusProvider');
  }
  return context;
};

interface ModelStatusProviderProps {
  children: ReactNode;
}

export const ModelStatusProvider: React.FC<ModelStatusProviderProps> = ({ children }) => {
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const checkModelStatus = async () => {
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
          model_name: 'Qwen/Qwen2.5-3B-Instruct'
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
        model_name: 'Qwen/Qwen2.5-3B-Instruct'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const refetch = useCallback(() => {
    checkModelStatus();
  }, []);

  useEffect(() => {
    // Verificar estado inicial
    checkModelStatus();
    
    // Crear un solo intervalo que se adapta al estado
    const intervalId = setInterval(() => {
      // Solo hacer polling si no estamos listos
      if (modelStatus?.status !== 'ready') {
        checkModelStatus();
      }
    }, 10000); // Polling cada 10 segundos solo cuando no está ready
    
    return () => {
      clearInterval(intervalId);
    };
  }, []); // Sin dependencias para evitar recrear el intervalo

  const contextValue: ModelStatusContextType = {
    modelStatus,
    isLoading,
    error,
    checkModelStatus,
    refetch,
  };

  return (
    <ModelStatusContext.Provider value={contextValue}>
      {children}
    </ModelStatusContext.Provider>
  );
};
