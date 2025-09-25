import React, { useState, useEffect } from 'react';
import { ArrowLeft, Moon, Sun } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { useModelStatus } from '../contexts/ModelStatusContext';

interface SettingsPageProps {
  onBack: () => void;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({ onBack }) => {
  const { isDarkMode, toggleTheme } = useTheme();
  const { modelStatus } = useModelStatus();
  const [appVersion, setAppVersion] = useState<string>('Cargando...');

  // Función para obtener información del modelo actual
  const getModelInfo = () => {
    if (!modelStatus) {
      return {
        name: 'Cargando...',
        description: 'Obteniendo información del modelo...',
        isLocal: true
      };
    }

    const modelName = modelStatus.model_name || 'Modelo desconocido';
    
    // Siempre mostrar Qwen2.5-3B ya que es el único modelo soportado
    if (modelName.includes('qwen') || modelName.includes('Qwen') || modelName.includes('Qwen2.5')) {
      return {
        name: 'Qwen2.5-3B-Instruct',
        description: 'Calyx AI utiliza el modelo Qwen2.5-3B-Instruct con cuantización 4-bit, que se ejecuta completamente en tu dispositivo para garantizar la privacidad de tus datos médicos.',
        isLocal: true
      };
    } else {
      // Fallback por si acaso, pero debería ser Qwen2.5-3B
      return {
        name: 'Qwen2.5-3B-Instruct',
        description: 'Calyx AI utiliza el modelo Qwen2.5-3B-Instruct con cuantización 4-bit, que se ejecuta completamente en tu dispositivo para garantizar la privacidad de tus datos médicos.',
        isLocal: true
      };
    }
  };

  const modelInfo = getModelInfo();

  // Cargar versión desde el backend
  useEffect(() => {
    const fetchVersion = async () => {
      try {
        const response = await fetch('http://localhost:8000/version');
        if (response.ok) {
          const data = await response.json();
          setAppVersion(data.version);
        } else {
          setAppVersion('1.7.3'); // Fallback
        }
      } catch (error) {
        console.error('Error fetching version:', error);
        setAppVersion('1.7.3'); // Fallback
      }
    };

    fetchVersion();
  }, []);

  return (
    <div className="flex flex-col h-screen bg-white dark:bg-gray-900 transition-colors">
      {/* Header */}
      <div className="flex items-center gap-4 p-6 border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={onBack}
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        >
          <ArrowLeft size={20} className="text-gray-600 dark:text-gray-400" />
        </button>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Configuraciones
        </h1>
      </div>

      {/* Content */}
      <div className="flex-1 p-6 overflow-y-auto">
        <div className="max-w-2xl space-y-6">
          
          {/* Apariencia Section */}
          <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Apariencia
            </h2>
            
            {/* Theme Toggle */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-white dark:bg-gray-700 rounded-lg">
                  {isDarkMode ? (
                    <Moon size={20} className="text-gray-700 dark:text-gray-300" />
                  ) : (
                    <Sun size={20} className="text-gray-700 dark:text-gray-300" />
                  )}
                </div>
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">
                    {isDarkMode ? 'Modo oscuro' : 'Modo claro'}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {isDarkMode 
                      ? 'Interfaz oscura para reducir el cansancio visual'
                      : 'Interfaz clara y brillante'
                    }
                  </p>
                </div>
              </div>
              
              {/* Switch Toggle */}
              <button
                onClick={toggleTheme}
                className={`
                  relative inline-flex h-7 w-12 items-center rounded-full transition-colors
                  ${isDarkMode 
                    ? 'bg-blue-600' 
                    : 'bg-gray-300 dark:bg-gray-600'
                  }
                `}
              >
                <span
                  className={`
                    inline-block h-5 w-5 transform rounded-full bg-white transition-transform
                    ${isDarkMode ? 'translate-x-6' : 'translate-x-1'}
                  `}
                />
              </button>
            </div>
          </div>

          {/* Estado del Modelo IA Section */}
          <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Estado del Modelo IA
            </h2>
            
            <div className="space-y-4">
              <div className="text-sm text-gray-600 dark:text-gray-400 bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
                <p className="font-medium text-blue-800 dark:text-blue-200 mb-1">
                  💡 Información sobre el modelo
                </p>
                <p>
                  {modelInfo.description}
                </p>
              </div>
            </div>
          </div>

          {/* Información Section */}
          <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Información
            </h2>
            
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Versión</span>
                <span className="text-gray-900 dark:text-white font-medium">{appVersion}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Modelo de IA</span>
                <span className="text-gray-900 dark:text-white font-medium">
                  {modelInfo.name} {modelInfo.isLocal ? '(Local)' : ''}
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Desarrollado por</span>
                <span className="text-gray-900 dark:text-white font-medium">✴ARCROSS</span>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};
