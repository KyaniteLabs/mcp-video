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
  FONT_MONO,
  TEXT,
  glowShadow,
} from '../lib/theme';
import { SPRING_SMOOTH } from '../lib/animations';

const EXTRACTED_COLORS = ['#CCFF00', '#7C3AED', '#5B2E91', '#00E5D4', '#8B5CF6'];

const CODE_LINES = [
  { text: 'from mcp_video import McpVideo', color: COLORS.VIOLET_BRIGHT },
  { text: '', color: '' },
  { text: 'video = McpVideo("input.mp4")', color: '' },
  { text: 'colors = video.extract_colors(', color: '' },
  { text: '    image="product.jpg",', color: COLORS.LIME },
  { text: '    n_colors=5', color: '#CCFF00' },
  { text: ')', color: '' },
  { text: '', color: '' },
  { text: 'print(colors.dominant)', color: COLORS.LIME },
  { text: '# => ["#CCFF00", "#7C3AED", ...]', color: COLORS.TEXT_MUTED },
];

export const S5ImageCode: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Wheel rotation
  const wheelAngle = frame * 1.5;

  // Swatch entrance
  const swatchSpring = spring({
    frame: Math.max(0, frame - 30),
    fps,
    config: SPRING_SMOOTH,
  });

  // Terminal cursor blink
  const cursorVisible = Math.floor(frame / 15) % 2 === 0;

  // Code line reveal
  const codeLineSpring = spring({
    frame: Math.max(0, frame - 60),
    fps,
    config: SPRING_SMOOTH,
  });

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
          display: 'flex',
          flexDirection: 'column',
          padding: 60,
          gap: 32,
        }}
      >
        {/* Header */}
        <div style={{ textAlign: 'center' }}>
          <div style={{
            ...TEXT.title,
            fontSize: 36,
            color: COLORS.VIOLET_BRIGHT,
            marginBottom: 8,
          }}>
            AI-Powered Color Analysis
          </div>
          <div style={{
            ...TEXT.subtitle,
            fontSize: 18,
            color: COLORS.TEXT_SECONDARY,
          }}>
            Extract brand colors from any image automatically
          </div>
        </div>

        {/* Main content - centered single column */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'row',
            justifyContent: 'center',
            alignItems: 'center',
            gap: 80,
            flex: 1,
          }}
        >
          {/* Left: Analysis demo */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 24,
          }}>
            {/* Image placeholder */}
            <div
              style={{
                width: 280,
                height: 180,
                borderRadius: 12,
                background: `linear-gradient(${135 + Math.sin(frame * 0.02) * 15}deg, #1a1a2e, #2d1b3d, #0f3460)`,
                border: `2px solid ${COLORS.VIOLET_MID}40`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                position: 'relative',
                overflow: 'hidden',
                boxShadow: `0 0 40px ${COLORS.VIOLET_MID}20`,
              }}
            >
              {/* Scan line */}
              <div
                style={{
                  position: 'absolute',
                  top: `${(frame * 1.5) % 180}px`,
                  left: 0,
                  right: 0,
                  height: 2,
                  background: `linear-gradient(90deg, transparent, ${COLORS.LIME}80, transparent)`,
                  boxShadow: `0 0 10px ${COLORS.LIME}`,
                }}
              />
              {/* Crosshair */}
              <div style={{
                position: 'absolute',
                width: 50,
                height: 50,
                border: `2px solid ${COLORS.LIME}60`,
                borderRadius: '50%',
              }} />
              <div style={{
                position: 'absolute',
                width: 1,
                height: 180,
                background: `${COLORS.VIOLET_MID}30`,
              }} />
              <div style={{
                position: 'absolute',
                height: 1,
                width: 280,
                background: `${COLORS.VIOLET_MID}30`,
              }} />
              <span style={{ 
                ...TEXT.caption,
                fontFamily: FONT_MONO,
                color: COLORS.LIME,
                fontSize: 14,
                letterSpacing: '0.2em',
              }}>
                ANALYZING
              </span>
            </div>

            {/* Swatches - centered, no offset */}
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 12,
            }}>
              <span style={{ 
                ...TEXT.overline,
                color: COLORS.TEXT_MUTED,
                fontSize: 12,
                letterSpacing: '0.15em',
              }}>
                EXTRACTED PALETTE
              </span>
              
              {/* Color circles in a row */}
              <div style={{
                display: 'flex',
                flexDirection: 'row',
                gap: 16,
                alignItems: 'center',
              }}>
                {EXTRACTED_COLORS.map((color, i) => {
                  const delay = i * 8;
                  const visible = frame > 30 + delay;
                  return (
                    <div
                      key={color + i}
                      style={{
                        width: 44,
                        height: 44,
                        borderRadius: '50%',
                        background: color,
                        opacity: visible ? 1 : 0,
                        transform: visible 
                          ? `scale(${interpolate(swatchSpring, [0, 1], [0.5, 1])})` 
                          : 'scale(0)',
                        boxShadow: `${glowShadow(color, 0.5)}, 0 4px 20px ${color}40`,
                        border: '3px solid rgba(255,255,255,0.15)',
                        transition: 'transform 0.3s ease',
                      }}
                    />
                  );
                })}
              </div>

              {/* Hex codes */}
              <div style={{
                display: 'flex',
                flexDirection: 'row',
                gap: 12,
              }}>
                {EXTRACTED_COLORS.map((color, i) => {
                  const hexOpacity = interpolate(frame, [60 + i * 5, 80 + i * 5], [0, 1], { 
                    extrapolateRight: 'clamp' 
                  });
                  return (
                    <span
                      key={color + i + 'hex'}
                      style={{
                        ...TEXT.code,
                        fontSize: 11,
                        color: color,
                        opacity: hexOpacity,
                        fontFamily: FONT_MONO,
                      }}
                    >
                      {color}
                    </span>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Right: Color wheel */}
          <div
            style={{
              width: 200,
              height: 200,
              borderRadius: '50%',
              background: `conic-gradient(
                from ${wheelAngle}deg,
                #ff0000, #ff8800, #ffff00, #00ff00,
                #00ffff, #0000ff, #ff00ff, #ff0000
              )`,
              opacity: interpolate(frame, [20, 50], [0, 1]),
              boxShadow: `0 0 60px ${COLORS.VIOLET_MID}30`,
              position: 'relative',
            }}
          >
            {/* Center cutout */}
            <div style={{
              position: 'absolute',
              width: 50,
              height: 50,
              borderRadius: '50%',
              background: COLORS.BG_DEEP,
              left: '50%',
              top: '50%',
              transform: 'translate(-50%, -50%)',
            }} />
          </div>
        </div>

        {/* Bottom: Code terminal */}
        <div
          style={{
            alignSelf: 'center',
            width: '100%',
            maxWidth: 600,
            borderRadius: 12,
            background: 'rgba(0,0,0,0.4)',
            border: `1px solid ${COLORS.VIOLET_MID}30`,
            padding: 20,
            opacity: interpolate(codeLineSpring, [0, 0.3], [0, 1]),
            transform: `translateY(${interpolate(codeLineSpring, [0, 1], [20, 0])}px)`,
          }}
        >
          {/* Window controls */}
          <div style={{ display: 'flex', flexDirection: 'row', gap: 6, marginBottom: 12 }}>
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#ff5f56' }} />
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#ffbd2e' }} />
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#27c93f' }} />
          </div>
          
          {/* Code lines */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {CODE_LINES.map((line, i) => {
              const lineDelay = Math.floor(i * 3);
              const lineVisible = frame > 60 + lineDelay;
              return (
                <div
                  key={i}
                  style={{
                    height: 22,
                    opacity: lineVisible ? 1 : 0,
                    fontFamily: FONT_MONO,
                    fontSize: 15,
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
                fontSize: 14,
                color: COLORS.LIME,
                opacity: cursorVisible ? 1 : 0,
              }}
            >
              █
            </span>
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
