import React, { useState, useEffect } from 'react';
import { useModelStatus } from '../contexts/ModelStatusContext';

interface BackendStartupStatus {
  status: 'starting' | 'dependencies' | 'loading_model' | 'ready' | 'error';
  progress_percentage: number;
  current_step: string;
  current_step_number: number;
  total_steps: number;
  error_message?: string;
}

interface BackendStartupProgressProps {
  onReady?: () => void;
  className?: string;
}

const BackendStartupProgress: React.FC<BackendStartupProgressProps> = ({ 
  onReady, 
  className = "" 
}) => {
  const [startupStatus, setStartupStatus] = useState<BackendStartupStatus | null>(null);
  const [isVisible, setIsVisible] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [attemptCount, setAttemptCount] = useState(0);
  const [startTime] = useState(Date.now());
  
  // Usar el contexto del modelo para coordinarse
  const { modelStatus } = useModelStatus();

  const checkStartupProgress = async () => {
    try {
      // Primer intento: usar el estado del modelo si está disponible
      if (modelStatus?.status === 'ready') {
        setStartupStatus({
          status: 'ready',
          progress_percentage: 100,
          current_step: 'Sistema listo',
          current_step_number: 4,
          total_steps: 4
        });
        onReady?.();
        setTimeout(() => setIsVisible(false), 1000);
        return;
      }

      const response = await fetch('http://localhost:8000/backend/startup/progress', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        timeout: 5000
      } as RequestInit);

      if (response.ok) {
        const data: BackendStartupStatus = await response.json();
        setStartupStatus(data);
        setHasError(false);
        setAttemptCount(0); // Reset counter on success

        // Si está listo, notificar y ocultar después de un momento
        if (data.status === 'ready') {
          onReady?.();
          setTimeout(() => setIsVisible(false), 1000);
        }
      } else {
        throw new Error('Backend no disponible');
      }
    } catch (error) {
      const currentAttempt = attemptCount + 1;
      setAttemptCount(currentAttempt);
      
      // Solo mostrar error después de 30 segundos Y varios intentos
      const elapsedTime = Date.now() - startTime;
      if (elapsedTime > 30000 && currentAttempt > 10) {
        setHasError(true);
        setStartupStatus({
          status: 'error',
          progress_percentage: 0,
          current_step: 'Error al conectar con el backend',
          current_step_number: 1,
          total_steps: 4,
          error_message: 'El backend no responde después de 30 segundos'
        });
      } else {
        // Mostrar estado de "esperando" mientras el backend inicia
        setStartupStatus({
          status: 'starting',
          progress_percentage: Math.round(Math.min((elapsedTime / 30000) * 100, 100)), // Progreso lineal de 0 a 100%
          current_step: elapsedTime < 10000 
            ? 'Iniciando backend...' 
            : elapsedTime < 20000 
            ? 'Cargando Python y dependencias...'
            : 'Preparando modelo de IA...',
          current_step_number: 1,
          total_steps: 4
        });
      }
    }
  };

  useEffect(() => {
    // Si el modelo ya está listo desde el contexto, no hacer nada más
    if (modelStatus?.status === 'ready') {
      setStartupStatus({
        status: 'ready',
        progress_percentage: 100,
        current_step: 'Sistema listo',
        current_step_number: 4,
        total_steps: 4
      });
      onReady?.();
      setTimeout(() => setIsVisible(false), 1000);
      return;
    }
    
    // Solo hacer una verificación inicial, sin polling constante
    checkStartupProgress();
    
    // Si el modelo no está listo después de 10 segundos, hacer una verificación más
    const timeoutId = setTimeout(() => {
      if (modelStatus?.status !== 'ready') {
        checkStartupProgress();
      }
    }, 10000);
    
    return () => {
      clearTimeout(timeoutId);
    };
  }, [modelStatus?.status]); // Solo reaccionar a cambios en el estado del modelo

  if (!isVisible || (!startupStatus && !hasError)) {
    return null;
  }

  const getProgressColor = () => {
    if (startupStatus?.status === 'error') return 'bg-red-500';
    if (startupStatus?.status === 'ready') return 'bg-green-500';
    return 'bg-blue-500';
  };

  const getStatusIcon = () => {
    switch (startupStatus?.status) {
      case 'starting':
        return '🚀';
      case 'dependencies':
        return '📦';
      case 'loading_model':
        return '🧠';
      case 'ready':
        return '✅';
      case 'error':
        return '❌';
      default:
        return '⏳';
    }
  };

  return (
    <div className={`bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 shadow-lg ${className}`}>
      <div className="flex items-center space-x-3 mb-4">
        <span className="text-2xl">{getStatusIcon()}</span>
        <div>
          <h3 className="font-semibold text-gray-900 dark:text-white">
            Iniciando Calyx AI Backend
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {startupStatus?.current_step || 'Conectando al backend...'}
          </p>
        </div>
      </div>

      {/* Barra de progreso - Solo porcentaje, sin pasos */}
      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Progreso
          </span>
          <span className="text-sm font-medium text-gray-900 dark:text-white">
            {Math.round(startupStatus?.progress_percentage || 0)}%
          </span>
        </div>
        
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
          <div 
            className={`h-3 rounded-full transition-all duration-500 ${getProgressColor()}`}
            style={{ width: `${Math.round(startupStatus?.progress_percentage || 0)}%` }}
          ></div>
        </div>
      </div>

      {/* Mensaje de estado */}
      <div className="mt-4">
        {startupStatus?.status === 'error' && (
          <div className="text-red-600 dark:text-red-400 text-sm">
            {startupStatus.error_message || 'Error desconocido'}
          </div>
        )}
        
        {startupStatus?.status === 'ready' && (
          <div className="text-green-600 dark:text-green-400 text-sm">
            ¡Backend iniciado correctamente!
          </div>
        )}
        
        {(startupStatus?.status === 'starting' || startupStatus?.status === 'dependencies' || startupStatus?.status === 'loading_model') && (
          <div className="text-blue-600 dark:text-blue-400 text-sm">
            Por favor espera mientras se inicia el sistema...
          </div>
        )}
      </div>
    </div>
  );
};

export default BackendStartupProgress;