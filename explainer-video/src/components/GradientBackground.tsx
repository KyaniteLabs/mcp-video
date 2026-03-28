import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from 'remotion';
import { COLORS } from '../lib/theme';
import { floatingDrift } from '../lib/animations';

interface GradientBackgroundProps {
  glowColor?: string;
  glowX?: number;
  glowY?: number;
  accentTint?: string;
}

const GradientBackground: React.FC<GradientBackgroundProps> = ({
  glowColor = COLORS.NEON_CYAN,
  glowX = 0.5,
  glowY = 0.5,
  accentTint,
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const driftX = floatingDrift(frame, 20, 0.02);
  const driftY = floatingDrift(frame, 15, 0.025);

  const tint = accentTint ?? glowColor;

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(ellipse at center, ${COLORS.BG_PRIMARY}, ${COLORS.BG_DEEP})`,
      }}
    >
      <div
        style={{
          position: 'absolute',
          width: '60%',
          height: '60%',
          left: `${glowX * 100}%`,
          top: `${glowY * 100}%`,
          transform: `translate(calc(-50% + ${driftX}px), calc(-50% + ${driftY}px))`,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${glowColor}15 0%, transparent 70%)`,
          opacity: 0.08,
          pointerEvents: 'none',
        }}
      />
      {/* Accent tint glow — second subtle layer for per-scene color identity */}
      {accentTint && (
        <div
          style={{
            position: 'absolute',
            width: '40%',
            height: '40%',
            left: `${(glowX + 0.1) * 100}%`,
            top: `${(glowY - 0.1) * 100}%`,
            transform: `translate(calc(-50% + ${driftX * 0.5}px), calc(-50% + ${driftY * 0.5}px))`,
            borderRadius: '50%',
            background: `radial-gradient(circle, ${tint}10 0%, transparent 70%)`,
            opacity: 0.12,
            pointerEvents: 'none',
          }}
        />
      )}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.3) 100%)',
          pointerEvents: 'none',
        }}
      />
    </AbsoluteFill>
  );
};

export default GradientBackground;
