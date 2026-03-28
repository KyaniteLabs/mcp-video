import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';
import { GRADIENT_PRIMARY, FONT_DISPLAY } from '../lib/theme';
import { EASE_OUT_EXPO } from '../lib/animations';

interface CounterProps {
  target: number;
  durationFrames: number;
}

export const Counter: React.FC<CounterProps> = ({ target, durationFrames }) => {
  const frame = useCurrentFrame();

  const value = interpolate(frame, [0, durationFrames], [0, target], {
    extrapolateRight: 'clamp',
    easing: EASE_OUT_EXPO,
  });

  const display = Math.round(value);

  return (
    <div
      style={{
        fontSize: 96,
        fontFamily: FONT_DISPLAY,
        fontWeight: 700,
        background: GRADIENT_PRIMARY,
        backgroundClip: 'text',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
      }}
    >
      {display}
    </div>
  );
};
