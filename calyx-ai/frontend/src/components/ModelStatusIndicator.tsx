import React, { useState } from 'react';
import { useModelStatus } from '../hooks/useModelStatus';
import ModelDownloadSplash from './ModelDownloadSplash';
import LoadingSpinner from './LoadingSpinner';

interface ModelStatusIndicatorProps {
  showDetails?: boolean;
  className?: string;
}

const ModelStatusIndicator: React.FC<ModelStatusIndicatorProps> = ({ 
  showDetails = false, 
  className = "" 
}) => {
  const { modelStatus, isLoading, error, refetch } = useModelStatus();
  const [showDownloadSplash, setShowDownloadSplash] = useState(false);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready':
        return 'text-green-500';
      case 'loading':
        return 'text-yellow-500';
      case 'not_downloaded':
        return 'text-orange-500';
      case 'error':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ready':
        return '✅';
      case 'loading':
        return <LoadingSpinner size="sm" />;
      case 'not_downloaded':
        return '📥';
      case 'error':
        return '❌';
      case 'checking':
        return <LoadingSpinner size="sm" />;
      default:
        return '❓';
    }
  };

  const formatSize = (sizeInMB: number) => {
    if (sizeInMB > 1024) {
      return `${(sizeInMB / 1024).toFixed(1)} GB`;
    }
    return `${sizeInMB.toFixed(0)} MB`;
  };

  if (isLoading && !modelStatus) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <span className="animate-pulse">🔍</span>
        <span className="text-gray-500">Verificando modelo...</span>
      </div>
    );
  }

  if (error && !modelStatus) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <span>❌</span>
        <span className="text-red-500">Error al verificar modelo</span>
        <button 
          onClick={refetch}
          className="text-blue-500 underline hover:text-blue-700"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!modelStatus) return null;

  return (
    <>
      <div className={`${className}`}>
        <div className="flex items-center space-x-2">
          <span>{getStatusIcon(modelStatus.status)}</span>
          <span className={getStatusColor(modelStatus.status)}>
            {modelStatus.message}
          </span>
          {modelStatus.status === 'error' && (
            <button 
              onClick={refetch}
              className="text-blue-500 underline hover:text-blue-700 text-sm"
            >
              Reintentar
            </button>
          )}
          {(modelStatus.status === 'not_downloaded' || modelStatus.status === 'error') && (
            <button 
              onClick={() => setShowDownloadSplash(true)}
              className="text-green-500 underline hover:text-green-700 text-sm ml-2"
            >
              Descargar modelo
            </button>
          )}
        </div>
        
        {showDetails && (
          <div className="mt-2 text-sm text-gray-600 dark:text-gray-400 space-y-1">
            <div>
              <strong>Modelo:</strong> {modelStatus.model_name?.split('/').pop() || 'N/A'}
            </div>
            {modelStatus.device && (
              <div>
                <strong>Dispositivo:</strong> {modelStatus.device.toUpperCase()}
              </div>
            )}
            {modelStatus.is_downloaded && modelStatus.cache_size_mb && modelStatus.cache_size_mb > 0 && (
              <div>
                <strong>Tamaño en cache:</strong> {formatSize(modelStatus.cache_size_mb)}
              </div>
            )}
            {modelStatus.status === 'not_downloaded' && (
              <div className="text-orange-600 dark:text-orange-400">
                <strong>Nota:</strong> El modelo se descargará automáticamente en el primer uso (~2-4 GB)
              </div>
            )}
          </div>
        )}
      </div>
      
      {/* Modal de descarga */}
      <ModelDownloadSplash
        isOpen={showDownloadSplash}
        onClose={() => setShowDownloadSplash(false)}
        onComplete={() => {
          setShowDownloadSplash(false);
          refetch(); // Actualizar el estado después de la descarga
        }}
      />
    </>
  );
};

export default ModelStatusIndicator;
