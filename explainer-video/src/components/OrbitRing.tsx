import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';

interface OrbitRingProps {
  items: React.ReactNode[];
  radius?: number;
  speed?: number;
}

export const OrbitRing: React.FC<OrbitRingProps> = ({
  items,
  radius = 200,
  speed = 0.01,
}) => {
  const frame = useCurrentFrame();

  const centerX = radius;
  const centerY = radius;

  return (
    <div
      style={{
        position: 'relative',
        width: radius * 2,
        height: radius * 2,
      }}
    >
      {items.map((item, i) => {
        const angle = ((2 * Math.PI) / items.length) * i + frame * speed;
        const x = centerX + radius * Math.cos(angle);
        const y = centerY + radius * Math.sin(angle);

        const localFrame = Math.max(0, frame - i * 8);
        const opacity = interpolate(localFrame, [0, 15], [0, 1], {
          extrapolateRight: 'clamp',
        });

        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: 0,
              top: 0,
              transform: `translate(${x}px, ${y}px) translate(-50%, -50%)`,
              opacity,
            }}
          >
            {item}
          </div>
        );
      })}
    </div>
  );
};
