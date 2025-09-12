import React, { useState } from 'react';

interface ThinkingDropdownProps {
  thinking: string;
  className?: string;
}

export default function ThinkingDropdown({ thinking, className = "" }: ThinkingDropdownProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!thinking || thinking.trim().length === 0) {
    return null;
  }

  return (
    <div className={`mb-3 ${className}`}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 px-3 py-2 text-sm bg-gray-100 dark:bg-gray-800 
                   text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 
                   dark:hover:bg-gray-700 transition-all duration-200 
                   border border-gray-200 dark:border-gray-600"
      >
        <span className="text-lg">🧠</span>
        <span className="font-medium">Thinking</span>
        <svg
          className={`w-4 h-4 transition-transform duration-200 ${
            isExpanded ? 'rotate-180' : ''
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>
      
      {isExpanded && (
        <div className="mt-2 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg 
                        border border-gray-200 dark:border-gray-700 
                        animate-in slide-in-from-top-2 duration-200">
          <div className="text-sm text-gray-600 dark:text-gray-400 font-mono 
                          whitespace-pre-wrap leading-relaxed">
            {thinking}
          </div>
        </div>
      )}
    </div>
  );
}
