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
import { SPRING_SMOOTH } from '../lib/animations';

const EXTRACTED_COLORS = ['#CCFF00', '#7C3AED', '#5B2E91', '#00E5D4', '#8B5CF6'];

const CODE_LINES = [
  { text: '// MCP Tool Call', color: COLORS.TEXT_MUTED },
  { text: 'video_extract_colors({', color: COLORS.VIOLET_BRIGHT },
  { text: '  input: "product.jpg",', color: COLORS.TEXT_PRIMARY },
  { text: '  n_colors: 5', color: COLORS.LIME },
  { text: '})', color: COLORS.TEXT_PRIMARY },
  { text: '', color: '' },
  { text: '// Response:', color: COLORS.TEXT_MUTED },
  { text: '["#CCFF00", "#7C3AED", ...]', color: COLORS.LIME },
];

const SCAN_SPEED = 1.5;
const SWATCH_SIZE = 48;
const CODE_START_FRAME = 60;

export const S5ImageCode: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({
    frame: Math.max(0, frame - 5),
    fps,
    config: SPRING_SMOOTH,
  });

  const swatchSpring = spring({
    frame: Math.max(0, frame - 30),
    fps,
    config: SPRING_SMOOTH,
  });

  const codeSpring = spring({
    frame: Math.max(0, frame - CODE_START_FRAME),
    fps,
    config: SPRING_SMOOTH,
  });

  const cursorVisible = Math.floor(frame / 15) % 2 === 0;

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.BG_DEEP }}>
      <GradientBackground
        glowColor={COLORS.VIOLET_MID}
        glowX={0.5}
        glowY={0.3}
        accentTint={COLORS.LIME}
      />

      <AbsoluteFill
        style={{
          padding: 60,
          flexDirection: 'column',
          gap: 32,
          alignItems: 'center',
        }}
      >
        {/* Title */}
        <div
          style={{
            ...TEXT.headline,
            fontSize: FONT_SIZE.HEADLINE,
            color: COLORS.TEXT_PRIMARY,
            textAlign: 'center',
            opacity: interpolate(titleSpring, [0, 0.3], [0, 1]),
            transform: `translateY(${interpolate(titleSpring, [0, 1], [20, 0])}px)`,
          }}
        >
          <span style={{ color: COLORS.VIOLET_BRIGHT }}>Image</span> Analysis
        </div>
        <div
          style={{
            ...TEXT.subtitle,
            fontSize: 18,
            color: COLORS.TEXT_SECONDARY,
            textAlign: 'center',
            opacity: interpolate(titleSpring, [0.3, 0.6], [0, 1]),
          }}
        >
          Extract brand colors from any image
        </div>

        {/* Two-column layout */}
        <div
          style={{
            flexDirection: 'row',
            justifyContent: 'center',
            alignItems: 'flex-start',
            gap: 60,
            flex: 1,
            width: '100%',
            maxWidth: 1000,
          }}
        >
          {/* Left: Image analysis + swatches */}
          <div style={{
            flexDirection: 'column',
            alignItems: 'center',
            gap: 20,
          }}>
            {/* Image with scan effect */}
            <div
              style={{
                width: 300,
                height: 200,
                borderRadius: 12,
                background: `linear-gradient(${135 + Math.sin(frame * 0.02) * 15}deg, #1a1a2e, #2d1b3d, #0f3460)`,
                border: `1px solid ${COLORS.VIOLET_MID}30`,
                position: 'relative',
                overflow: 'hidden',
                opacity: interpolate(titleSpring, [0.2, 0.5], [0, 1]),
              }}
            >
              {/* Scan line */}
              <div
                style={{
                  position: 'absolute',
                  top: `${(frame * SCAN_SPEED) % 200}px`,
                  left: 0,
                  right: 0,
                  height: 2,
                  background: `linear-gradient(90deg, transparent, ${COLORS.LIME}80, transparent)`,
                  boxShadow: `0 0 8px ${COLORS.LIME}`,
                }}
              />
              <span style={{
                ...TEXT.caption,
                fontFamily: FONT_MONO,
                color: COLORS.LIME,
                fontSize: 13,
                position: 'absolute',
                bottom: 12,
                left: 16,
                letterSpacing: '0.15em',
              }}>
                ANALYZING
              </span>
            </div>

            {/* Extracted palette */}
            <div style={{
              flexDirection: 'column',
              alignItems: 'center',
              gap: 12,
            }}>
              <span style={{
                ...TEXT.overline,
                color: COLORS.TEXT_MUTED,
                fontSize: 11,
                letterSpacing: '0.15em',
              }}>
                EXTRACTED PALETTE
              </span>

              <div style={{
                flexDirection: 'row',
                gap: 14,
                alignItems: 'center',
              }}>
                {EXTRACTED_COLORS.map((color, i) => {
                  const visible = frame > 30 + i * 8;
                  return (
                    <div key={color} style={{
                      width: SWATCH_SIZE,
                      height: SWATCH_SIZE,
                      borderRadius: '50%',
                      background: color,
                      opacity: visible ? interpolate(swatchSpring, [0, 1], [0, 1]) : 0,
                      transform: visible
                        ? `scale(${interpolate(swatchSpring, [0, 1], [0.4, 1])})`
                        : 'scale(0)',
                      boxShadow: `0 0 12px ${color}50`,
                      border: '2px solid rgba(255,255,255,0.15)',
                    }} />
                  );
                })}
              </div>

              {/* Hex codes */}
              <div style={{ flexDirection: 'row', gap: 14 }}>
                {EXTRACTED_COLORS.map((color, i) => (
                  <span
                    key={`hex-${color}`}
                    style={{
                      fontFamily: FONT_MONO,
                      fontSize: 10,
                      color: color,
                      opacity: interpolate(frame, [60 + i * 5, 80 + i * 5], [0, 1], {
                        extrapolateRight: 'clamp',
                      }),
                      width: SWATCH_SIZE,
                      textAlign: 'center',
                    }}
                  >
                    {color}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Right: Code terminal */}
          <div
            style={{
              width: 420,
              borderRadius: 12,
              background: 'rgba(0,0,0,0.5)',
              border: `1px solid ${COLORS.VIOLET_MID}20`,
              padding: 20,
              opacity: interpolate(codeSpring, [0, 0.3], [0, 1]),
              transform: `translateY(${interpolate(codeSpring, [0, 1], [20, 0])}px)`,
            }}
          >
            {/* Window controls */}
            <div style={{ flexDirection: 'row', gap: 6, marginBottom: 14 }}>
              <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#ff5f56' }} />
              <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#ffbd2e' }} />
              <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#27c93f' }} />
            </div>

            {/* Code lines */}
            <div style={{ flexDirection: 'column', gap: 2 }}>
              {CODE_LINES.map((line, i) => {
                const lineVisible = frame > CODE_START_FRAME + i * 3;
                return (
                  <div
                    key={i}
                    style={{
                      height: 22,
                      opacity: lineVisible ? 1 : 0,
                      fontFamily: FONT_MONO,
                      fontSize: 14,
                      color: line.color || COLORS.TEXT_PRIMARY,
                    }}
                  >
                    {line.text}
                  </div>
                );
              })}
              <span
                style={{
                  fontFamily: FONT_MONO,
                  fontSize: 14,
                  color: COLORS.LIME,
                  opacity: cursorVisible ? 1 : 0,
                }}
              >
                █
              </span>
            </div>
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
