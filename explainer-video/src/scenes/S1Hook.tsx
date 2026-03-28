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
import {
  COLORS,
  glowShadow,
  FONT_DISPLAY,
  FONT_MONO,
  TEXT,
} from '../lib/theme';
import {
  SPRING_SLAM,
  useAmbientMotion,
} from '../lib/animations';

const HOOK_TEXT = 'What if AI could edit video?';
const TAGLINE = 'The video editing MCP server for AI agents';

export const S1Hook: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { breathe } = useAmbientMotion(frame);

  // Phase 1 (0-15): Black screen with blinking cursor
  const cursorVisible = Math.floor(frame / 8) % 2 === 0;

  // Phase 2 (15-30): Flash "CLI video editing is broken"
  const hookOpacity = interpolate(frame, [15, 18], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const hookExitOpacity = interpolate(frame, [45, 55], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const hookGlitch = frame >= 15 && frame < 25
    ? Math.random() > 0.7 ? Math.random() * 4 - 2 : 0
    : 0;

  // Phase 3 (30-60): Logo slam
  const logoScale = spring({
    frame: Math.max(0, frame - 30),
    fps,
    config: SPRING_SLAM,
  });
  const logoBlur = interpolate(logoScale, [0, 0.7, 1], [12, 3, 0]);
  const logoOpacity = interpolate(frame, [28, 32], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Brackets animate fast (0.3s = 9 frames)
  const bracketProgress = interpolate(frame, [32, 41], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Phase 4 (60-90): Underline sweep + tagline
  const underlineProgress = interpolate(frame, [55, 70], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const taglineOpacity = interpolate(frame, [65, 72], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Background pulse
  const bgOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.BG_DEEP }}>
      <div style={{ opacity: bgOpacity }}>
        <GradientBackground glowColor={COLORS.NEON_CYAN} />
      </div>

      <ParticleField count={30} />

      <AbsoluteFill
        style={{
          justifyContent: 'center',
          alignItems: 'center',
          flexDirection: 'column',
        }}
      >
        {/* Blinking cursor (frames 0-15) */}
        {frame < 18 && (
          <div style={{ opacity: frame < 15 ? 1 : 0, height: 40 }}>
            <span
              style={{
                ...TEXT.code,
                fontSize: 32,
                color: COLORS.NEON_CYAN,
              }}
            >
              {cursorVisible ? '▊' : ' '}
            </span>
          </div>
        )}

        {/* Hook text flash (frames 15-55) */}
        <div
          style={{
            opacity: hookOpacity * hookExitOpacity,
            position: 'absolute',
            transform: `translateX(${hookGlitch}px)`,
          }}
        >
          <span
            style={{
              ...TEXT.codeBold,
              fontSize: 48,
              color: COLORS.NEON_ORANGE,
              textShadow: glowShadow(COLORS.NEON_ORANGE, 0.8),
            }}
          >
            {HOOK_TEXT}
          </span>
        </div>

        {/* Logo slam (frames 30-90) */}
        <div
          style={{
            opacity: logoOpacity,
            transform: `scale(${logoScale * breathe})`,
            position: 'relative',
            padding: 40,
          }}
        >
          {/* Corner brackets */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: `${bracketProgress * 30}px`,
              height: `${bracketProgress * 30}px`,
              borderTop: `2px solid ${COLORS.NEON_CYAN}`,
              borderLeft: `2px solid ${COLORS.NEON_CYAN}`,
            }}
          />
          <div
            style={{
              position: 'absolute',
              top: 0,
              right: 0,
              width: `${bracketProgress * 30}px`,
              height: `${bracketProgress * 30}px`,
              borderTop: `2px solid ${COLORS.NEON_CYAN}`,
              borderRight: `2px solid ${COLORS.NEON_CYAN}`,
            }}
          />
          <div
            style={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              width: `${bracketProgress * 30}px`,
              height: `${bracketProgress * 30}px`,
              borderBottom: `2px solid ${COLORS.NEON_MAGENTA}`,
              borderLeft: `2px solid ${COLORS.NEON_MAGENTA}`,
            }}
          />
          <div
            style={{
              position: 'absolute',
              bottom: 0,
              right: 0,
              width: `${bracketProgress * 30}px`,
              height: `${bracketProgress * 30}px`,
              borderBottom: `2px solid ${COLORS.NEON_MAGENTA}`,
              borderRight: `2px solid ${COLORS.NEON_MAGENTA}`,
            }}
          />

          <GlowText
            style={{
              fontSize: 96,
              fontWeight: 700,
              textAlign: 'center',
              fontFamily: FONT_DISPLAY,
              letterSpacing: '-0.03em',
              filter: `blur(${logoBlur}px)`,
            }}
          >
            mcp-video
          </GlowText>

          {/* Animated underline */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              marginTop: 8,
            }}
          >
            <div
              style={{
                width: `${underlineProgress * 100}%`,
                maxWidth: 480,
                height: 3,
                background: `linear-gradient(90deg, ${COLORS.NEON_CYAN}, ${COLORS.NEON_MAGENTA})`,
                boxShadow: glowShadow(COLORS.NEON_CYAN),
                borderRadius: 2,
              }}
            />
          </div>
        </div>

        {/* Tagline (frames 65-90) */}
        <div
          style={{
            marginTop: 16,
            fontSize: 24,
            color: COLORS.TEXT_SECONDARY,
            textAlign: 'center',
            opacity: taglineOpacity,
            fontFamily: FONT_DISPLAY,
          }}
        >
          {TAGLINE}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
