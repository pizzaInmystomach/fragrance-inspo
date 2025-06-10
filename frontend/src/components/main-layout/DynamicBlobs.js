import React, { useMemo } from 'react';
import styles from './DynamicBlobs.module.css';


export default function DynamicBlobsBackground({ children, className = "" }) {
  const blobs = useMemo(() => 
    Array.from({ length: 25 }, (_, i) => ({
      id: i,
      x: Math.random() * 150 - 10,
      y: Math.random() * 150 - 10,
      size: Math.random() * 360 + 320,
      blur: Math.random() * 60 + 55,
                opacity: Math.random() * 0.20 + 0.30,
      duration: Math.random() * 10 + 10,
      delay: Math.random() * 10,
      borderRadius: `${Math.random() * 30 + 40}% ${Math.random() * 30 + 40}% ${Math.random() * 30 + 40}% ${Math.random() * 30 + 40}%`,
      colorIndex: Math.floor(Math.random() * 6),
      moveX: (Math.random() - 0.5) * 300,
      moveY: (Math.random() - 0.5) * 300,
      scale: Math.random() * 0.4 + 0.8,
      rotateEnd: Math.random() * 360 + 180
    })), []
  );

  const colors = [
    'linear-gradient(135deg, #E8D5FF 0%, #DCC4FF 50%, #D1B3FF 100%)', // 淡紫色
    'linear-gradient(135deg, #F0E6FF 0%, #E8D5FF 50%, #E0CCFF 100%)', // 更淡的紫色
    'linear-gradient(135deg, #FFE1F0 0%, #FFCCE5 50%, #FFB3D9 100%)', // 淡粉色
    'linear-gradient(135deg, #F0E6FF 0%, #FFE1F0 50%, #E8D5FF 100%)', // 紫粉色
    'linear-gradient(135deg, #E1F0FF 0%, #CCE5FF 50%, #B3D9FF 100%)', // 淡藍色
    'linear-gradient(135deg, #E8D5FF 0%, #E1F0FF 50%, #DCC4FF 100%)'  // 紫藍色
  ];

  return (
    <div className={`${styles.blobsContainer} ${className}`}>
      <div className={styles.blobsBackground}>
        {blobs.map((blob) => (
          <div
            key={blob.id}
            className={styles.blob}
            style={{
              '--start-x': `${blob.x}%`,
              '--start-y': `${blob.y}%`,
              '--move-x': `${blob.moveX}px`,
              '--move-y': `${blob.moveY}px`,
              '--size': `${blob.size}px`,
              '--blur': `${blob.blur}px`,
              '--opacity': blob.opacity,
              '--duration': `${blob.duration}s`,
              '--delay': `${blob.delay}s`,
              '--border-radius': blob.borderRadius,
              '--background': colors[blob.colorIndex],
              '--scale': blob.scale,
              '--rotate': `${blob.rotateEnd}deg`
            }}
          />
        ))}
      </div>
      
      <div className={styles.contentWrapper}>
        {children}
      </div>
    </div>
  );
}