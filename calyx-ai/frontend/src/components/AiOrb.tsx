import React, { useEffect, useState } from 'react';
import './AiOrb.css';

interface AiOrbProps {
  isActive?: boolean;
  size?: 'small' | 'medium' | 'large';
}

const AiOrb: React.FC<AiOrbProps> = ({ isActive = false, size = 'medium' }) => {
  const [isLightMode, setIsLightMode] = useState(false);

  useEffect(() => {
    // Detectar tema de manera más simple
    const checkTheme = () => {
      // Verificar si hay clase 'dark' en el documentElement
      const hasDarkClass = document.documentElement.classList.contains('dark');
      // Si no hay clase dark, asumir light mode
      setIsLightMode(!hasDarkClass);
    };

    checkTheme();
    
    // Observer solo para cambios en la clase del documento
    const observer = new MutationObserver(checkTheme);
    observer.observe(document.documentElement, { 
      attributes: true, 
      attributeFilter: ['class'] 
    });

    return () => {
      observer.disconnect();
    };
  }, []);

  const sizeClasses = {
    small: 'w-8 h-8',
    medium: 'w-12 h-12',
    large: 'w-16 h-16'
  };

  const themeClass = isLightMode ? 'light-theme' : 'dark-theme';

  return (
    <div className={`ai-orb-wrapper ${sizeClasses[size]} ${isActive ? 'processing' : 'standby'}`}>
      <div className="orb-container">
        <div className={`glass-orb ${themeClass}`}>
          <div className="aura-core"></div>
          <div className="aura-layer aura-layer-1"></div>
          <div className="aura-layer aura-layer-2"></div>
          <div className="aura-layer aura-layer-3"></div>
          <div className="plasma-effect">
            <div className="plasma-bubble plasma-1"></div>
            <div className="plasma-bubble plasma-2"></div>
            <div className="plasma-bubble plasma-3"></div>
          </div>
          <div className="energy-field">
            <div className="micro-particle"></div>
            <div className="micro-particle"></div>
            <div className="micro-particle"></div>
            <div className="micro-particle"></div>
            <div className="micro-particle"></div>
          </div>
          <div className="resonance-ring"></div>
          <div className="heat-distortion"></div>
        </div>
      </div>
    </div>
  );
};

export default AiOrb;