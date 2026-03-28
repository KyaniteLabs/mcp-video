import React from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';
import { COLORS, FONT_MONO } from '../lib/theme';
import { SPRING_BOUNCE } from '../lib/animations';

interface ColorSwatchProps {
  color: string;
  label?: string;
  delay?: number;
}

export const ColorSwatch: React.FC<ColorSwatchProps> = ({
  color,
  label,
  delay = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const localFrame = Math.max(0, frame - delay);
  const sp = spring({
    frame: localFrame,
    fps,
    config: SPRING_BOUNCE,
  });

  const scale = interpolate(sp, [0, 1], [0, 1]);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 8,
      }}
    >
      <div
        style={{
          width: 80,
          height: 80,
          borderRadius: '50%',
          backgroundColor: color,
          boxShadow: `0 0 20px ${color}60`,
          transform: `scale(${scale})`,
        }}
      />
      <span
        style={{
          fontSize: 14,
          fontFamily: FONT_MONO,
          color: COLORS.TEXT_SECONDARY,
          textAlign: 'center',
        }}
      >
        {label ?? color}
      </span>
    </div>
  );
};
