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
        bottom: 60,
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
          fontFamily: "'Inter', 'system-ui', sans-serif",
          fontSize: 36,
          fontWeight: 700,
          color: '#ffffff',
          letterSpacing: '0.01em',
          lineHeight: 1.2,
          textShadow: '0 1px 4px rgba(0,0,0,0.8)',
          whiteSpace: 'nowrap',
        }}
      >
        {text}
      </span>
    </div>
  );
};
