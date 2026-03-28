import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from 'remotion';
import GradientBackground from '../components/GradientBackground';
import ParticleField from '../components/ParticleField';
import {
  COLORS,
  GRADIENT_PRIMARY,
  FONT_SIZE,
  FONT_DISPLAY,
  TEXT,
  glowShadow,
} from '../lib/theme';
import { SPRING_SMOOTH, useAmbientMotion } from '../lib/animations';

const ORBIT_LABELS = [
  'trim', 'merge', 'filter', 'overlay',
  'convert', 'watermark', 'fade', 'blur',
];

export const S2Solution: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { breathe } = useAmbientMotion(frame);

  // Counter: 0 → 43 over 120 frames
  const counterValue = Math.min(
    43,
    Math.floor(interpolate(frame, [0, 120], [0, 43], {
      extrapolateRight: 'clamp',
    })),
  );

  // Counter entrance
  const counterSpring = spring({
    frame,
    fps,
    config: { damping: 30, stiffness: 100, mass: 0.6 },
  });

  // Subtitle entrance
  const subtitleSpring = spring({
    frame: Math.max(0, frame - 15),
    fps,
    config: SPRING_SMOOTH,
  });

  // Orbit rotation
  const orbitAngle = (frame * 0.75) * (Math.PI / 180);

  // Background glow intensifies with counter
  const glowIntensity = interpolate(counterValue, [0, 43], [0.06, 0.2]);

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.BG_DEEP }}>
      <GradientBackground glowColor={COLORS.NEON_CYAN} />
      <ParticleField count={20} />

      <AbsoluteFill
        style={{
          justifyContent: 'center',
          alignItems: 'center',
          flexDirection: 'column',
        }}
      >
        {/* Hero counter */}
        <div
          style={{
            opacity: interpolate(counterSpring, [0, 0.3], [0, 1]),
            transform: `scale(${interpolate(counterSpring, [0, 1], [0.8, 1]) * breathe})`,
          }}
        >
          <span
            style={{
              ...TEXT.display,
              fontSize: FONT_SIZE.DISPLAY,
              background: GRADIENT_PRIMARY,
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              filter: `drop-shadow(0 0 20px ${COLORS.NEON_CYAN}30)`,
            }}
          >
            {counterValue}
          </span>
        </div>

        {/* Subtitle */}
        <div
          style={{
            marginTop: 16,
            fontSize: FONT_SIZE.SUBTITLE,
            color: COLORS.NEON_CYAN,
            opacity: interpolate(subtitleSpring, [0, 0.3], [0, 1]),
            transform: `translateY(${interpolate(subtitleSpring, [0, 1], [12, 0])}px)`,
          }}
        >
          43 video editing tools
        </div>

        {/* Orbit ring */}
        <div
          style={{
            position: 'absolute',
            width: 500,
            height: 500,
            borderRadius: '50%',
            border: `1px solid rgba(0,240,255,0.1)`,
          }}
        >
          {/* Orbit dots */}
          {ORBIT_LABELS.map((label, i) => {
            const angle = orbitAngle + (i * (2 * Math.PI)) / ORBIT_LABELS.length;
            const radius = 240;
            const x = Math.cos(angle) * radius;
            const y = Math.sin(angle) * radius;
            const isAtTop = Math.sin(angle) < -0.7;
            const glowStrength = isAtTop ? 0.6 : 0.2;

            return (
              <div
                key={label}
                style={{
                  position: 'absolute',
                  left: '50%',
                  top: '50%',
                  transform: `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                }}
              >
                <div
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    background: COLORS.NEON_CYAN,
                    boxShadow: glowShadow(COLORS.NEON_CYAN, glowStrength),
                  }}
                />
                <span
                  style={{
                    ...TEXT.caption,
                    color: COLORS.TEXT_MUTED,
                    fontSize: 15,
                  }}
                >
                  {label}
                </span>
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
