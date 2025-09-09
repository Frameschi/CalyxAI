import React from 'react';
import { MessageSquarePlus, Settings } from 'lucide-react';

interface SidebarProps {
  onNewChat: () => void;
  onOpenSettings: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ 
  onNewChat, 
  onOpenSettings 
}) => {
  return (
    <div className="fixed left-0 top-0 h-full w-80 bg-white dark:bg-gray-900 shadow-lg border-r border-gray-200 dark:border-gray-700 z-40">
      {/* Header */}
      <div className="flex items-center p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <img 
            src="./logo.png" 
            alt="Calyx AI Logo" 
            className="w-12 h-12 object-contain"
          />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Calyx AI
          </h2>
        </div>
      </div>

      {/* Content Container */}
      <div className="flex flex-col h-[calc(100vh-81px)]">
        {/* Top Menu Items */}
        <div className="p-4">
          {/* Nuevo Chat */}
          <button
            onClick={onNewChat}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-left"
          >
            <MessageSquarePlus size={20} className="text-gray-600 dark:text-gray-400" />
            <span className="text-gray-900 dark:text-white font-medium">
              Nuevo chat
            </span>
          </button>
        </div>

        {/* Spacer to push settings to bottom */}
        <div className="flex-1"></div>

        {/* Bottom Menu Items */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          {/* Configuraciones */}
          <button
            onClick={onOpenSettings}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-left"
          >
            <Settings size={20} className="text-gray-600 dark:text-gray-400" />
            <span className="text-gray-900 dark:text-white font-medium">
              Configuraciones
            </span>
          </button>
        </div>
      </div>
    </div>
  );
};
