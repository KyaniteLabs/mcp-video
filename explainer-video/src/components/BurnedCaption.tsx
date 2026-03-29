import React from 'react';
import { interpolate, useCurrentFrame } from 'remotion';
import { COLORS } from '../lib/theme';

interface BurnedCaptionProps {
  text: string;
  delay?: number;
}

export const BurnedCaption: React.FC<BurnedCaptionProps> = ({ text, delay = 0 }) => {
  const frame = useCurrentFrame();
  const captionOpacity = interpolate(frame, [delay, delay + 10], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 80,
        left: '50%',
        transform: 'translateX(-50%)',
        background: 'rgba(0,0,0,0.65)',
        borderRadius: 12,
        padding: '10px 24px',
        maxWidth: 800,
        zIndex: 50,
        pointerEvents: 'none',
        opacity: captionOpacity,
      }}
    >
      <span
        style={{
          fontFamily: "'JetBrains Mono', 'SF Mono', 'Fira Code', monospace",
          fontSize: 32,
          fontWeight: 600,
          color: '#E2E8F0',
          letterSpacing: '-0.02em',
          lineHeight: 1.3,
          textShadow: `
            0 0 20px rgba(204,255,0,0.3),
            0 0 40px rgba(124,58,237,0.2),
            0 2px 4px rgba(0,0,0,0.8)
          `,
          whiteSpace: 'nowrap',
        }}
      >
        {text}
      </span>
    </div>
  );
};
