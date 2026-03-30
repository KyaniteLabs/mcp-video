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
  { value: '82', label: 'Tools' },
  { value: '690+', label: 'Tests' },
  { value: 'Apache 2.0', label: 'License' },
];

export const S10CTA: React.FC = () => {
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
    82,
    Math.floor(interpolate(frame, [40, 80], [0, 82], {
      extrapolateRight: 'clamp',
    })),
  );

  // Typewriter effect for pip install
  const pipText = 'pip install mcp-video';
  const charsTyped = Math.min(
    pipText.length,
    Math.floor(interpolate(frame, [25, 50], [0, pipText.length], {
      extrapolateRight: 'clamp',
    })),
  );

  // Fade to black over last 45 frames (frame 275-320)
  const fadeToBlack = interpolate(frame, [275, 320], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.BG_DEEP }}>
      <div style={{ opacity: 1 - fadeToBlack }}>
        <GradientBackground glowColor={COLORS.LIME} />
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

        {/* Terminal with pip install — typewriter effect */}
        <div
          style={{
            opacity: interpolate(terminalSpring, [0, 0.3], [0, 1]),
            transform: `translateY(${interpolate(terminalSpring, [0, 1], [20, 0])}px)`,
            background: 'rgba(0,0,0,0.5)',
            borderRadius: 12,
            padding: '20px 32px',
            border: '1px solid rgba(255,255,255,0.06)',
            position: 'relative',
          }}
        >
          <div
            style={{
              fontFamily: FONT_MONO,
              fontSize: 24,
              color: COLORS.TEXT_PRIMARY,
            }}
          >
            <span style={{ color: COLORS.LIME }}>$</span>{' '}
            <span style={{ color: COLORS.TEXT_PRIMARY }}>
              {pipText.slice(0, charsTyped)}
            </span>
            <span style={{
              color: COLORS.LIME,
              opacity: charsTyped >= pipText.length ? (cursorVisible ? 1 : 0) : 1,
            }}>
              {' '}█
            </span>
          </div>

          {/* "Copied!" confirmation after typing */}
          {frame > 60 && (
            <div
              style={{
                position: 'absolute',
                top: -16,
                right: 0,
                opacity: interpolate(frame, [60, 70], [0, 1], {
                  extrapolateLeft: 'clamp',
                  extrapolateRight: 'clamp',
                }),
                ...TEXT.caption,
                fontSize: 14,
                color: COLORS.NEON_GREEN,
              }}
            >
              ✓ Copied!
            </div>
          )}
        </div>

        {/* Stat cards - horizontal row with larger numbers */}
        <div
          style={{
            flexDirection: 'row',
            gap: 32,
            opacity: interpolate(statsSpring, [0, 0.3], [0, 1]),
            transform: `translateY(${interpolate(statsSpring, [0, 1], [16, 0])}px)`,
          }}
        >
          {STATS.map((stat, i) => {
            // Animated counter for each stat
            const animatedValue = stat.label === 'Tools'
              ? Math.min(82, Math.floor(interpolate(frame, [40 + i * 10, 70 + i * 10], [0, 82], { extrapolateRight: 'clamp' })))
              : stat.label === 'Tests'
              ? Math.min(690, Math.floor(interpolate(frame, [40 + i * 10, 70 + i * 10], [0, 690], { extrapolateRight: 'clamp' })))
              : stat.value;
            
            return (
              <GlassCard
                key={stat.label}
                accentColor={COLORS.LIME}
                accentTop
                style={{ 
                  padding: '28px 56px',
                  minWidth: 160,
                }}
              >
                <div style={{ textAlign: 'center' }}>
                  <div
                    style={{
                      ...TEXT.display,
                      fontSize: stat.label === 'License' ? 32 : 56,
                      background: GRADIENT_PRIMARY,
                      backgroundClip: 'text',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      marginBottom: 8,
                    }}
                  >
                    {stat.label === 'License' ? stat.value : animatedValue + (stat.label === 'Tests' ? '+' : '')}
                  </div>
                  <div
                    style={{
                      ...TEXT.caption,
                      fontSize: 14,
                      color: COLORS.TEXT_MUTED,
                      letterSpacing: '0.1em',
                    }}
                  >
                    {stat.label}
                  </div>
                </div>
              </GlassCard>
            );
          })}
        </div>

        {/* GitHub URL pill with underline sweep */}
        <div
          style={{
            opacity: interpolate(pillSpring, [0, 0.3], [0, 1]),
            transform: `translateY(${interpolate(pillSpring, [0, 1], [12, 0])}px)`,
            background: 'rgba(27,28,30,0.7)',
            borderRadius: 999,
            padding: '10px 28px',
            border: '1px solid rgba(255,255,255,0.08)',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Underline sweep */}
          <div
            style={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              height: 2,
              width: `${interpolate(frame, [70, 90], [0, 100], { extrapolateRight: 'clamp' })}%`,
              background: COLORS.LIME,
              borderRadius: 1,
            }}
          />
          <span
            style={{
              fontFamily: FONT_MONO,
              fontSize: 16,
              color: COLORS.LIME,
              position: 'relative',
              zIndex: 1,
            }}
          >
            github.com/simonbraz/mcp-video
          </span>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
