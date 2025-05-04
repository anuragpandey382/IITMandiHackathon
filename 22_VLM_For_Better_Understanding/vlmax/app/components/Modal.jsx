import React, { useEffect, useState, useRef } from 'react';

export default function Modal({ isOpen, onClose, url, type }) {
  if (!isOpen) return null;
  
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const imageRef = useRef(null);
  
  useEffect(() => {
    if (!isOpen) return;
    
    const originalStyle = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    
    const updateDimensions = () => {
      setDimensions({
        width: window.visualViewport
        ? window.visualViewport.width
        : window.innerWidth,
        height: window.visualViewport
        ? window.visualViewport.height
        : window.innerHeight
      });
    };
    console.log('Window dimensions:', dimensions);
    
    updateDimensions();
    console.log('Initial dimensions:', dimensions);
    
    window.addEventListener('resize', updateDimensions);
    
    return () => {
      document.body.style.overflow = originalStyle;
      window.removeEventListener('resize', updateDimensions);
    };
  }, [isOpen]);
  
  useEffect(() => {
    if (imageRef.current && type === 'image') {
      const img = imageRef.current;
      
      const handleImageLoad = () => {
        setDimensions(prev => ({...prev}));
      };
      
      img.addEventListener('load', handleImageLoad);
      return () => {
        img.removeEventListener('load', handleImageLoad);
      };
    }
  }, [imageRef.current, type]);

  const getModalStyle = () => {
    const style = {
      position: 'absolute',
      backgroundColor: 'transparent',
      boxSizing: 'border-box',
      zIndex: 10000,
    };
    
    style.top = '50%';
    style.left = '50%';
    style.transform = 'translate(-50%, -50%)';
    
    style.maxWidth = '90vw';
    style.maxHeight = '80vh';
    
    return style;
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
      onClick={onClose}
    >
      <div 
        style={getModalStyle()}
        onClick={(e) => e.stopPropagation()}
      >
        <button
          style={{
            position: 'absolute',
            top: '-40px',
            right: '-40px',
            width: '30px',
            height: '30px',
            borderRadius: '50%',
            backgroundColor: 'white',
            display: 'flex',
            alignItems: 'start',
            justifyContent: 'center',
            cursor: 'pointer',
            fontSize: '20px',
            fontWeight: 'bold',
            border: 'none',
            zIndex: 10001,
            padding: 0,
            lineHeight: '30px'
          }}
          onClick={onClose}
          aria-label="Close"
        >
          ×
        </button>

        {type === 'image' && (
          <img
            ref={imageRef}
            src={url}
            alt="Preview"
            style={{
              maxWidth: '90vw',
              maxHeight: '80vh',
              objectFit: 'contain',
              boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
              display: 'block'
            }}
          />
        )}

        {type === 'html' && (
          <iframe
            src={url}
            title="HTML Preview"
            style={{ 
              width: '90vw', 
              height: '80vh', 
              border: 'none' 
            }}
          />
        )}

        {type === 'csv' && (
          <div 
            style={{ 
              backgroundColor: 'white', 
              padding: '20px', 
              borderRadius: '8px', 
              overflow: 'auto', 
              maxHeight: '80vh', 
              maxWidth: '90vw' 
            }}
          >
            <object
              data={url}
              type="text/csv"
              style={{ width: '100%', height: '100%' }}
            >
              <p>Unable to preview CSV.</p>
            </object>
          </div>
        )}
      </div>
    </div>
  );
}