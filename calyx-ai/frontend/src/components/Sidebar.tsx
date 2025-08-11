import React from 'react';
import { MessageSquarePlus, Settings, X } from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onNewChat: () => void;
  onOpenSettings: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ 
  isOpen, 
  onClose, 
  onNewChat, 
  onOpenSettings 
}) => {
  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <div className={`
        fixed left-0 top-0 h-full w-80 bg-white dark:bg-gray-900 shadow-lg 
        border-r border-gray-200 dark:border-gray-700 transition-transform duration-300 z-50
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <img 
              src="/logo.png" 
              alt="Calyx AI Logo" 
              className="w-8 h-8 object-contain"
            />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Calyx AI
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors lg:hidden"
          >
            <X size={20} className="text-gray-600 dark:text-gray-400" />
          </button>
        </div>

        {/* Menu Items */}
        <div className="p-4 space-y-2">
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
    </>
  );
};
