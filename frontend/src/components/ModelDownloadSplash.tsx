import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Download, X, AlertCircle, CheckCircle } from 'lucide-react';
import { useModelDownload } from '../hooks/useModelDownload';
import LoadingSpinner from './LoadingSpinner';

interface ModelDownloadSplashProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete?: () => void;
  autoStart?: boolean;
}

const ModelDownloadSplash: React.FC<ModelDownloadSplashProps> = ({
  isOpen,
  onClose,
  onComplete,
  autoStart = false
}) => {
  const { 
    downloadProgress, 
    isDownloading, 
    error, 
    startDownload, 
    cancelDownload, 
    resetDownload 
  } = useModelDownload();

  // Auto-iniciar descarga si está habilitado
  useEffect(() => {
    if (isOpen && autoStart && downloadProgress.status === 'idle') {
      startDownload();
    }
  }, [isOpen, autoStart, downloadProgress.status, startDownload]);

  // Llamar onComplete cuando la descarga termine
  useEffect(() => {
    if (downloadProgress.status === 'completed' && onComplete) {
      setTimeout(() => {
        onComplete();
      }, 2000); // Esperar 2 segundos para mostrar el éxito
    }
  }, [downloadProgress.status, onComplete]);

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatTime = (seconds: number): string => {
    if (seconds === Infinity || isNaN(seconds) || seconds <= 0) return 'Calculando...';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${remainingSeconds}s`;
    } else {
      return `${remainingSeconds}s`;
    }
  };

  const formatSpeed = (bytesPerSecond: number): string => {
    return `${formatBytes(bytesPerSecond)}/s`;
  };

  const getStatusIcon = () => {
    switch (downloadProgress.status) {
      case 'downloading':
        return <LoadingSpinner size="md" />;
      case 'completed':
        return <CheckCircle className="text-green-500" size={24} />;
      case 'error':
      case 'cancelled':
        return <AlertCircle className="text-red-500" size={24} />;
      default:
        return <Download size={24} />;
    }
  };

  const getStatusMessage = () => {
    switch (downloadProgress.status) {
      case 'downloading':
        return 'Descargando modelo Qwen2.5-3B...';
      case 'completed':
        return '¡Descarga completada!';
      case 'error':
        return 'Error en la descarga';
      case 'cancelled':
        return 'Descarga cancelada';
      default:
        return 'Preparando descarga del modelo IA';
    }
  };

  const handleClose = () => {
    if (isDownloading) {
      cancelDownload();
    }
    if (downloadProgress.status !== 'idle') {
      resetDownload();
    }
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-md w-full p-6 relative"
          >
            {/* Botón de cerrar */}
            <button
              onClick={handleClose}
              className="absolute top-4 right-4 p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition-colors"
              disabled={isDownloading}
            >
              <X size={20} className="text-gray-500 dark:text-gray-400" />
            </button>

            {/* Header */}
            <div className="text-center mb-6">
              <div className="flex justify-center mb-4">
                <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-full">
                  {getStatusIcon()}
                </div>
              </div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                {getStatusMessage()}
              </h2>
              <p className="text-gray-600 dark:text-gray-400 text-sm">
                {downloadProgress.status === 'idle' && 
                  'Calyx AI necesita descargar el modelo Qwen2.5-3B para funcionar localmente.'}
                {downloadProgress.status === 'downloading' && 
                  'Esto puede tomar unos minutos dependiendo de tu conexión.'}
                {downloadProgress.status === 'completed' && 
                  'El modelo está listo para usar. ¡Disfruta de Calyx AI!'}
                {downloadProgress.status === 'error' && 
                  `Error: ${error}`}
                {downloadProgress.status === 'cancelled' && 
                  'Puedes reiniciar la descarga cuando lo desees.'}
              </p>
            </div>

            {/* Progress Section */}
            {(downloadProgress.status === 'downloading' || downloadProgress.status === 'completed') && (
              <div className="mb-6">
                {/* Progress Bar */}
                <div className="mb-4">
                  <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-2">
                    <span>{downloadProgress.percentage}%</span>
                    <span>
                      {formatBytes(downloadProgress.downloadedBytes)} / {formatBytes(downloadProgress.totalBytes)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                    <motion.div
                      className="bg-blue-500 h-3 rounded-full relative overflow-hidden"
                      initial={{ width: 0 }}
                      animate={{ width: `${downloadProgress.percentage}%` }}
                      transition={{ duration: 0.3 }}
                    >
                      {/* Shimmer effect */}
                      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white via-transparent opacity-20 animate-pulse" />
                    </motion.div>
                  </div>
                </div>

                {/* Download Stats */}
                {downloadProgress.status === 'downloading' && (
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Velocidad:</span>
                      <div className="font-medium text-gray-900 dark:text-white">
                        {formatSpeed(downloadProgress.downloadSpeed)}
                      </div>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Tiempo restante:</span>
                      <div className="font-medium text-gray-900 dark:text-white">
                        {formatTime(downloadProgress.timeRemaining)}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3">
              {downloadProgress.status === 'idle' && (
                <>
                  <button
                    onClick={onClose}
                    className="flex-1 py-3 px-4 rounded-xl border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    Más tarde
                  </button>
                  <button
                    onClick={startDownload}
                    className="flex-1 py-3 px-4 rounded-xl bg-blue-500 text-white hover:bg-blue-600 transition-colors font-medium"
                  >
                    Descargar ahora
                  </button>
                </>
              )}

              {downloadProgress.status === 'downloading' && (
                <button
                  onClick={cancelDownload}
                  className="flex-1 py-3 px-4 rounded-xl border border-red-300 dark:border-red-600 text-red-700 dark:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                >
                  Cancelar descarga
                </button>
              )}

              {(downloadProgress.status === 'error' || downloadProgress.status === 'cancelled') && (
                <>
                  <button
                    onClick={handleClose}
                    className="flex-1 py-3 px-4 rounded-xl border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    Cerrar
                  </button>
                  <button
                    onClick={() => {
                      resetDownload();
                      startDownload();
                    }}
                    className="flex-1 py-3 px-4 rounded-xl bg-blue-500 text-white hover:bg-blue-600 transition-colors font-medium"
                  >
                    Reintentar
                  </button>
                </>
              )}

              {downloadProgress.status === 'completed' && (
                <button
                  onClick={onClose}
                  className="flex-1 py-3 px-4 rounded-xl bg-green-500 text-white hover:bg-green-600 transition-colors font-medium"
                >
                  Continuar
                </button>
              )}
            </div>

            {/* Footer Info */}
            {downloadProgress.status === 'idle' && (
              <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <p className="text-xs text-blue-800 dark:text-blue-200">
                  💡 <strong>Privacidad garantizada:</strong> El modelo se ejecuta completamente en tu dispositivo. 
                  Tus datos médicos nunca salen de tu computadora.
                </p>
              </div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default ModelDownloadSplash;
