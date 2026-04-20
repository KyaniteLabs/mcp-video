import React from 'react';
import { interpolate, useCurrentFrame } from 'remotion';
import { COLORS, FONT_MONO } from '../lib/theme';

interface BurnedCaptionProps {
  text: string;
  delay?: number;
}

export const BurnedCaption: React.FC<BurnedCaptionProps> = ({ text, delay = 0 }) => {
  const frame = useCurrentFrame();
  const captionOpacity = interpolate(frame, [delay, delay + 8], [0, 1], {
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
        background: 'rgba(0,0,0,0.7)',
        borderRadius: 8,
        padding: '8px 20px',
        maxWidth: 900,
        zIndex: 50,
        pointerEvents: 'none',
        opacity: captionOpacity,
      }}
    >
      <span
        style={{
          fontFamily: FONT_MONO,
          fontSize: 20,
          fontWeight: 500,
          color: COLORS.TEXT_PRIMARY,
          letterSpacing: '-0.01em',
          lineHeight: 1.4,
          whiteSpace: 'normal',
          wordBreak: 'break-word',
        }}
      >
        {text}
      </span>
    </div>
  );
};
