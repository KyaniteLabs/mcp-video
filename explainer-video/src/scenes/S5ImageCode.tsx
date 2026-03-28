import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from 'remotion';
import GradientBackground from '../components/GradientBackground';
import {
  COLORS,
  FONT_SIZE,
  FONT_MONO,
  TEXT,
  glowShadow,
} from '../lib/theme';
import { SPRING_SMOOTH, stagger, useAmbientMotion } from '../lib/animations';

const EXTRACTED_COLORS = ['#FF6B35', '#00F0FF', '#8B5CF6', '#00FF88', '#FF00FF'];
const HARMONY_LABELS = ['Complementary', 'Analogous', 'Triadic'];

const CODE_LINES = [
  { text: 'from mcp_video import McpVideo', color: COLORS.NEON_MAGENTA },
  { text: '', color: '' },
  { text: 'video = McpVideo("input.mp4")', color: '' },
  { text: 'colors = video.extract_colors(', color: '' },
  { text: '    image="product.jpg",', color: COLORS.NEON_CYAN },
  { text: '    n_colors=5', color: '#FF6B35' },
  { text: ')', color: '' },
  { text: '', color: '' },
  { text: 'print(colors.dominant)', color: COLORS.NEON_GREEN },
  { text: '# => [("#FF6B35", 35%), ...]', color: COLORS.TEXT_MUTED },
];

export const S5ImageCode: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { drift } = useAmbientMotion(frame);

  // Wheel rotation
  const wheelAngle = frame * 2;

  // Swatch expansion
  const swatchSpread = interpolate(frame, [0, 60], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Terminal cursor blink
  const cursorVisible = Math.floor(frame / 15) % 2 === 0;

  // Color swatch bob
  const swatchBob = Math.sin(frame * 0.06) * 4;

  // Gradient shift from magenta to cyan
  const gradientMix = interpolate(frame, [0, 240], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Code line reveal
  const codeLineSpring = spring({
    frame: Math.max(0, frame - 30),
    fps,
    config: SPRING_SMOOTH,
  });

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.BG_DEEP }}>
      <GradientBackground
        glowColor={COLORS.NEON_MAGENTA}
        glowX={0.5}
        glowY={0.3}
        accentTint={COLORS.NEON_CYAN}
      />

      <AbsoluteFill
        style={{
          padding: 80,
          flexDirection: 'column',
          gap: 40,
        }}
      >
        {/* Top: Product image placeholder with swatches */}
        <div
          style={{
            flexDirection: 'row',
            alignItems: 'center',
            gap: 40,
          }}
        >
          {/* Image placeholder with gradient animation */}
          <div
            style={{
              width: 300,
              height: 200,
              borderRadius: 12,
              background: `linear-gradient(${135 + Math.sin(frame * 0.015) * 20}deg, #1a1a2e, #2d1b3d, #0f3460)`,
              border: '1px solid rgba(255,255,255,0.08)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            {/* Scan line effect */}
            <div
              style={{
                position: 'absolute',
                top: `${(frame * 2) % 200}px`,
                left: 0,
                right: 0,
                height: 2,
                background: `linear-gradient(90deg, transparent, ${COLORS.NEON_MAGENTA}40, transparent)`,
              }}
            />
            {/* Crosshair */}
            <div style={{
              position: 'absolute',
              width: 40,
              height: 40,
              border: `1px solid ${COLORS.NEON_MAGENTA}30`,
              borderRadius: '50%',
            }} />
            <div style={{
              position: 'absolute',
              width: 1,
              height: 200,
              background: `${COLORS.NEON_MAGENTA}15`,
            }} />
            <div style={{
              position: 'absolute',
              height: 1,
              width: 300,
              background: `${COLORS.NEON_MAGENTA}15`,
            }} />
            <span style={{ ...TEXT.caption, color: COLORS.NEON_MAGENTA, fontSize: 12, opacity: 0.6 }}>
              ANALYZING
            </span>
          </div>

          {/* Swatch circles */}
          <div style={{ flexDirection: 'column', gap: 12 }}>
            <span style={{ ...TEXT.overline, color: COLORS.TEXT_MUTED, fontSize: 12, marginBottom: 8 }}>
              EXTRACTED PALETTE
            </span>
            <div style={{ flexDirection: 'row', gap: 12, alignItems: 'center' }}>
              {EXTRACTED_COLORS.map((color, i) => {
                const offset = (i - 2) * swatchSpread * 50;
                return (
                  <div
                    key={color}
                    style={{
                      width: 48,
                      height: 48,
                      borderRadius: '50%',
                      background: color,
                      transform: `translateX(${offset}px) translateY(${swatchBob}px)`,
                      boxShadow: glowShadow(color, 0.4),
                      border: '2px solid rgba(255,255,255,0.1)',
                    }}
                  />
                );
              })}
            </div>
          </div>

          {/* Color wheel */}
          <div
            style={{
              width: 180,
              height: 180,
              borderRadius: '50%',
              background: `conic-gradient(
                #ff0000, #ff8800, #ffff00, #00ff00,
                #00ffff, #0000ff, #ff00ff, #ff0000
              )`,
              transform: `rotate(${wheelAngle}deg)`,
              opacity: 0.8,
              flexShrink: 0,
              position: 'relative',
            }}
          >
            {/* Harmony labels around wheel */}
            {HARMONY_LABELS.map((label, i) => {
              const angle = (i * 120 + wheelAngle) * (Math.PI / 180);
              const x = Math.cos(angle) * 110;
              const y = Math.sin(angle) * 110;
              return (
                <span
                  key={label}
                  style={{
                    ...TEXT.caption,
                    fontSize: 10,
                    color: COLORS.TEXT_MUTED,
                    position: 'absolute',
                    left: '50%',
                    top: '50%',
                    transform: `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {label}
                </span>
              );
            })}
          </div>
        </div>

        {/* Bottom: Terminal with syntax-highlighted code */}
        <div
          style={{
            flex: 1,
            borderRadius: 12,
            background: 'rgba(0,0,0,0.5)',
            border: '1px solid rgba(255,255,255,0.06)',
            padding: 24,
            opacity: interpolate(codeLineSpring, [0, 0.3], [0, 1]),
            transform: `translateY(${interpolate(codeLineSpring, [0, 1], [20, 0])}px)`,
          }}
        >
          <div style={{ flexDirection: 'row', gap: 6, marginBottom: 16 }}>
            <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#ff5f56' }} />
            <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#ffbd2e' }} />
            <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#27c93f' }} />
          </div>
          {CODE_LINES.map((line, i) => {
            const lineDelay = Math.floor(i * 4);
            const lineVisible = frame > 30 + lineDelay;
            return (
              <div
                key={i}
                style={{
                  height: 24,
                  opacity: lineVisible ? 1 : 0,
                  fontFamily: FONT_MONO,
                  fontSize: 17,
                  color: line.color || COLORS.TEXT_PRIMARY,
                  letterSpacing: '0',
                }}
              >
                {line.text}
              </div>
            );
          })}
          <span
            style={{
              fontFamily: FONT_MONO,
              fontSize: 15,
              color: COLORS.NEON_CYAN,
              opacity: cursorVisible ? 1 : 0,
            }}
          >
            ▊
          </span>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
