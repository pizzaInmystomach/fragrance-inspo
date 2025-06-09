import React, { useMemo } from 'react';

export default function DynamicBlobsBackground({ children, className = "" }) {
  // 生成25个blob的配置
  const blobs = useMemo(() => 
    Array.from({ length: 25 }, (_, i) => ({
      id: i,
      x: Math.random() * 150 - 10, // 限制在容器内
      y: Math.random() * 150 - 10,
      size: Math.random() * 360 + 320,
      blur: Math.random() * 60 + 55,
                opacity: Math.random() * 0.25 + 0.35, // 更低的透明度
      duration: Math.random() * 10 + 10,
      delay: Math.random() * 10,
      borderRadius: `${Math.random() * 30 + 40}% ${Math.random() * 30 + 40}% ${Math.random() * 30 + 40}% ${Math.random() * 30 + 40}%`,
      colorIndex: Math.floor(Math.random() * 6),
      moveX: (Math.random() - 0.5) * 300, // 减少移动范围
      moveY: (Math.random() - 0.5) * 300, // 减少移动范围
      scale: Math.random() * 0.4 + 0.8,
      rotateEnd: Math.random() * 360 + 180 // 旋转角度
    })), []
  );

  // 淡色系：淡紫、淡粉、淡蓝
  const colors = [
    'linear-gradient(135deg, #E8D5FF 0%, #DCC4FF 50%, #D1B3FF 100%)', // 淡紫色
    'linear-gradient(135deg, #F0E6FF 0%, #E8D5FF 50%, #E0CCFF 100%)', // 更淡的紫色
    'linear-gradient(135deg, #FFE1F0 0%, #FFCCE5 50%, #FFB3D9 100%)', // 淡粉色
    'linear-gradient(135deg, #F0E6FF 0%, #FFE1F0 50%, #E8D5FF 100%)', // 紫粉渐变
    'linear-gradient(135deg, #E1F0FF 0%, #CCE5FF 50%, #B3D9FF 100%)', // 淡蓝色
    'linear-gradient(135deg, #E8D5FF 0%, #E1F0FF 50%, #DCC4FF 100%)'  // 紫蓝渐变
  ];

  return (
    <div className={`blobs-container ${className}`}>
      <div className="blobs-background">
        {blobs.map((blob) => (
          <div
            key={blob.id}
            className="blob"
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
      
      <div className="content-wrapper">
        {children}
      </div>

      <style jsx>{`
        .blobs-container {
          position: relative;
          min-height: 100vh;
        }

        .blobs-background {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          pointer-events: none;
          z-index: 0;
        }

        .blob {
          position: absolute;
          left: var(--start-x);
          top: var(--start-y);
          width: var(--size);
          height: var(--size);
          background: var(--background);
          border-radius: var(--border-radius);
          filter: blur(var(--blur));
          opacity: var(--opacity);
          animation: blobMovement var(--duration) ease-in-out infinite var(--delay);
          will-change: transform;
        }

        .content-wrapper {
          position: relative;
          z-index: 1;
        }

        @keyframes blobMovement {
          0% {
            transform: translate(0, 0) scale(var(--scale)) rotate(0deg);
          }
          25% {
            transform: translate(calc(var(--move-x) * 0.3), calc(var(--move-y) * 0.5)) 
                      scale(calc(var(--scale) * 1.1)) rotate(calc(var(--rotate) * 0.25));
          }
          50% {
            transform: translate(var(--move-x), var(--move-y)) 
                      scale(calc(var(--scale) * 0.9)) rotate(calc(var(--rotate) * 0.5));
          }
          75% {
            transform: translate(calc(var(--move-x) * 0.7), calc(var(--move-y) * 0.3)) 
                      scale(calc(var(--scale) * 1.05)) rotate(calc(var(--rotate) * 0.75));
          }
          100% {
            transform: translate(0, 0) scale(var(--scale)) rotate(var(--rotate));
          }
        }
      `}</style>
    </div>
  );
}