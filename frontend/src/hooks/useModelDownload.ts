import { useState, useCallback, useRef } from 'react';

interface DownloadProgress {
  percentage: number;
  downloadedBytes: number;
  totalBytes: number;
  downloadSpeed: number; // bytes per second
  timeRemaining: number; // seconds
  status: 'idle' | 'downloading' | 'completed' | 'error' | 'cancelled';
}

interface UseModelDownloadReturn {
  downloadProgress: DownloadProgress;
  isDownloading: boolean;
  error: string | null;
  startDownload: () => Promise<void>;
  cancelDownload: () => void;
  resetDownload: () => void;
}

export const useModelDownload = (): UseModelDownloadReturn => {
  const [downloadProgress, setDownloadProgress] = useState<DownloadProgress>({
    percentage: 0,
    downloadedBytes: 0,
    totalBytes: 0,
    downloadSpeed: 0,
    timeRemaining: 0,
    status: 'idle'
  });
  
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const startTimeRef = useRef<number>(0);
  const lastProgressTimeRef = useRef<number>(0);
  const lastDownloadedBytesRef = useRef<number>(0);

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatTime = (seconds: number): string => {
    if (seconds === Infinity || isNaN(seconds)) return 'Calculando...';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${remainingSeconds}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${remainingSeconds}s`;
    } else {
      return `${remainingSeconds}s`;
    }
  };

  const calculateSpeed = (downloadedBytes: number, currentTime: number): number => {
    if (lastProgressTimeRef.current === 0) {
      lastProgressTimeRef.current = currentTime;
      lastDownloadedBytesRef.current = downloadedBytes;
      return 0;
    }

    const timeDiff = (currentTime - lastProgressTimeRef.current) / 1000; // seconds
    const bytesDiff = downloadedBytes - lastDownloadedBytesRef.current;
    
    if (timeDiff > 0) {
      const speed = bytesDiff / timeDiff;
      lastProgressTimeRef.current = currentTime;
      lastDownloadedBytesRef.current = downloadedBytes;
      return speed;
    }
    
    return 0;
  };

  const startDownload = useCallback(async () => {
    try {
      setError(null);
      abortControllerRef.current = new AbortController();
      startTimeRef.current = Date.now();
      lastProgressTimeRef.current = 0;
      lastDownloadedBytesRef.current = 0;

      setDownloadProgress(prev => ({
        ...prev,
        status: 'downloading',
        percentage: 0,
        downloadedBytes: 0,
        totalBytes: 0,
        downloadSpeed: 0,
        timeRemaining: 0
      }));

      // Simular descarga progresiva para el demo
      // En una implementación real, esto sería una llamada al backend
      const totalSize = 2400000000; // 2.4 GB aproximado para Qwen2.5-3B
      
      setDownloadProgress(prev => ({
        ...prev,
        totalBytes: totalSize
      }));

      // Simular descarga por chunks
      const chunkSize = totalSize / 100; // 1% por chunk
      let downloadedBytes = 0;

      for (let i = 0; i <= 100; i++) {
        // Verificar si se canceló
        if (abortControllerRef.current?.signal.aborted) {
          setDownloadProgress(prev => ({
            ...prev,
            status: 'cancelled'
          }));
          return;
        }

        downloadedBytes = Math.min(i * chunkSize, totalSize);
        const currentTime = Date.now();
        const speed = calculateSpeed(downloadedBytes, currentTime);
        const remaining = speed > 0 ? (totalSize - downloadedBytes) / speed : 0;

        setDownloadProgress(prev => ({
          ...prev,
          percentage: Math.round((downloadedBytes / totalSize) * 100),
          downloadedBytes,
          downloadSpeed: speed,
          timeRemaining: remaining
        }));

        // Simular velocidad de descarga variable (más lento al principio, más rápido después)
        const baseDelay = 100;
        const variableDelay = Math.max(50, 200 - (i * 2)); // Se acelera con el tiempo
        await new Promise(resolve => setTimeout(resolve, baseDelay + variableDelay));
      }

      // Descarga completada
      setDownloadProgress(prev => ({
        ...prev,
        status: 'completed',
        percentage: 100,
        downloadedBytes: totalSize,
        timeRemaining: 0
      }));

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido durante la descarga');
      setDownloadProgress(prev => ({
        ...prev,
        status: 'error'
      }));
    }
  }, []);

  const cancelDownload = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setDownloadProgress(prev => ({
      ...prev,
      status: 'cancelled'
    }));
  }, []);

  const resetDownload = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setDownloadProgress({
      percentage: 0,
      downloadedBytes: 0,
      totalBytes: 0,
      downloadSpeed: 0,
      timeRemaining: 0,
      status: 'idle'
    });
    setError(null);
  }, []);

  return {
    downloadProgress,
    isDownloading: downloadProgress.status === 'downloading',
    error,
    startDownload,
    cancelDownload,
    resetDownload,
  };
};
