import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from 'remotion';
import GradientBackground from '../components/GradientBackground';
import GlowText from '../components/GlowText';
import ParticleField from '../components/ParticleField';
import GlassCard from '../components/GlassCard';
import {
  COLORS,
  GRADIENT_PRIMARY,
  FONT_SIZE,
  FONT_DISPLAY,
  FONT_MONO,
  TEXT,
  glowShadow,
} from '../lib/theme';
import { SPRING_SMOOTH, SPRING_BOUNCE, useAmbientMotion } from '../lib/animations';

const STATS = [
  { value: '43', label: 'Tools' },
  { value: '545+', label: 'Tests' },
  { value: 'Apache 2.0', label: 'License' },
];

export const S8CTA: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { breathe, drift } = useAmbientMotion(frame);

  // Logo pulse
  const logoPulse = spring({
    frame,
    fps,
    config: SPRING_BOUNCE,
  });

  // Terminal entrance
  const terminalSpring = spring({
    frame: Math.max(0, frame - 20),
    fps,
    config: SPRING_SMOOTH,
  });

  // Stats entrance
  const statsSpring = spring({
    frame: Math.max(0, frame - 40),
    fps,
    config: SPRING_SMOOTH,
  });

  // GitHub pill entrance
  const pillSpring = spring({
    frame: Math.max(0, frame - 55),
    fps,
    config: SPRING_SMOOTH,
  });

  // Cursor blink
  const cursorVisible = Math.floor(frame / 15) % 2 === 0;

  // Counter micro-tick on stat values
  const statCounter = Math.min(
    43,
    Math.floor(interpolate(frame, [40, 80], [0, 43], {
      extrapolateRight: 'clamp',
    })),
  );

  // Fade to black over last 45 frames (frame 165-210)
  const fadeToBlack = interpolate(frame, [165, 210], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.BG_DEEP }}>
      <div style={{ opacity: 1 - fadeToBlack }}>
        <GradientBackground glowColor={COLORS.NEON_CYAN} />
      </div>

      <ParticleField count={25} />

      {/* Fade overlay */}
      {fadeToBlack > 0 && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: COLORS.BG_DEEP,
            opacity: fadeToBlack,
            pointerEvents: 'none',
            zIndex: 100,
          }}
        />
      )}

      <AbsoluteFill
        style={{
          justifyContent: 'center',
          alignItems: 'center',
          flexDirection: 'column',
          gap: 40,
        }}
      >
        {/* Pulsing logo */}
        <div
          style={{
            transform: `scale(${interpolate(logoPulse, [0, 1], [0.9, 1]) * breathe})`,
          }}
        >
          <GlowText
            style={{
              fontSize: 72,
              fontWeight: 700,
              textAlign: 'center',
              fontFamily: FONT_DISPLAY,
            }}
          >
            mcp-video
          </GlowText>
        </div>

        {/* Terminal with pip install */}
        <div
          style={{
            opacity: interpolate(terminalSpring, [0, 0.3], [0, 1]),
            transform: `translateY(${interpolate(terminalSpring, [0, 1], [20, 0])}px)`,
            background: 'rgba(0,0,0,0.5)',
            borderRadius: 12,
            padding: '20px 32px',
            border: '1px solid rgba(255,255,255,0.06)',
          }}
        >
          <div
            style={{
              fontFamily: FONT_MONO,
              fontSize: 24,
              color: COLORS.TEXT_PRIMARY,
            }}
          >
            <span style={{ color: COLORS.NEON_GREEN }}>$</span>{' '}
            pip install mcp-video
            <span style={{ color: COLORS.NEON_CYAN, opacity: cursorVisible ? 1 : 0 }}>
              {' '}▊
            </span>
          </div>
        </div>

        {/* Stat cards */}
        <div
          style={{
            flexDirection: 'row',
            gap: 24,
            opacity: interpolate(statsSpring, [0, 0.3], [0, 1]),
            transform: `translateY(${interpolate(statsSpring, [0, 1], [16, 0])}px)`,
          }}
        >
          {STATS.map((stat, i) => (
            <GlassCard
              key={stat.label}
              accentColor={COLORS.NEON_CYAN}
              accentTop
              style={{ padding: '20px 48px' }}
            >
              <div style={{ textAlign: 'center' }}>
                <div
                  style={{
                    ...TEXT.display,
                    fontSize: stat.label === 'License' ? 28 : 48,
                    background: GRADIENT_PRIMARY,
                    backgroundClip: 'text',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    marginBottom: 4,
                  }}
                >
                  {stat.label === 'Tools' ? statCounter : stat.value}
                </div>
                <div
                  style={{
                    ...TEXT.caption,
                    fontSize: 14,
                    color: COLORS.TEXT_MUTED,
                  }}
                >
                  {stat.label}
                </div>
              </div>
            </GlassCard>
          ))}
        </div>

        {/* GitHub URL pill */}
        <div
          style={{
            opacity: interpolate(pillSpring, [0, 0.3], [0, 1]),
            transform: `translateY(${interpolate(pillSpring, [0, 1], [12, 0])}px)`,
            background: 'rgba(27,28,30,0.7)',
            borderRadius: 999,
            padding: '10px 28px',
            border: '1px solid rgba(255,255,255,0.08)',
          }}
        >
          <span
            style={{
              fontFamily: FONT_MONO,
              fontSize: 16,
              color: COLORS.NEON_CYAN,
            }}
          >
            github.com/simonbraz/mcp-video
          </span>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
