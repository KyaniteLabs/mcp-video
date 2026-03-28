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
  TEXT,
  glowShadow,
  FONT_DISPLAY,
} from '../lib/theme';
import { SPRING_SMOOTH, stagger, useAmbientMotion } from '../lib/animations';

const NODES = [
  { label: 'Chroma Key', icon: '🎬' },
  { label: 'Overlay', icon: '🖼️' },
  { label: 'Stabilize', icon: '📐' },
  { label: 'Watermark', icon: '💎' },
  { label: 'Subtitles', icon: '📝' },
  { label: 'Speed', icon: '⏩' },
];

export const S4ProFeatures: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { shimmer } = useAmbientMotion(frame);

  // Node entrance
  const nodeSpring = spring({
    frame: Math.max(0, frame - 10),
    fps,
    config: SPRING_SMOOTH,
  });

  // Traveling wave pulse across nodes
  const pulseIndex = Math.floor(frame / 15) % NODES.length;

  // Waveform bars
  const waveformBars = 24;
  const waveformHeights = Array.from({ length: waveformBars }, (_, i) =>
    interpolate(
      Math.sin(frame * 0.1 + i * 0.4),
      [-1, 1],
      [8, 60],
    ),
  );

  // Ken Burns pan
  const kbX = interpolate(frame, [0, 210], [0, 40]);
  const kbScale = interpolate(frame, [0, 210], [1.0, 1.15]);

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.BG_DEEP }}>
      <GradientBackground
        glowColor={COLORS.NEON_PURPLE}
        glowX={0.5}
        glowY={0.45}
      />

      <AbsoluteFill
        style={{
          padding: 80,
          flexDirection: 'column',
        }}
      >
        {/* Title */}
        <div
          style={{
            ...TEXT.headline,
            fontSize: FONT_SIZE.HEADLINE,
            color: COLORS.TEXT_PRIMARY,
            textAlign: 'center',
            marginBottom: 60,
            opacity: interpolate(nodeSpring, [0, 0.3], [0, 1]),
          }}
        >
          <span style={{ color: COLORS.NEON_PURPLE }}>Pro</span> Features
        </div>

        {/* Center: Radial node graph */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            position: 'relative',
          }}
        >
          {/* Hub */}
          <div
            style={{
              position: 'absolute',
              width: 100,
              height: 100,
              borderRadius: '50%',
              background: `radial-gradient(circle, ${COLORS.NEON_PURPLE}30, ${COLORS.BG_CARD})`,
              border: `2px solid ${COLORS.NEON_PURPLE}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: glowShadow(COLORS.NEON_PURPLE, 0.4),
              opacity: interpolate(nodeSpring, [0, 0.5], [0, 1]),
            }}
          >
            <span style={{ ...TEXT.badge, color: COLORS.NEON_PURPLE, fontSize: 16 }}>
              PRO
            </span>
          </div>

          {/* Nodes arranged in circle */}
          {NODES.map((node, i) => {
            const angle = (i * 360) / NODES.length - 90;
            const rad = (angle * Math.PI) / 180;
            const radius = 240;
            const x = Math.cos(rad) * radius;
            const y = Math.sin(rad) * radius;
            const isPulsing = pulseIndex === i;

            const nodeDelay = spring({
              frame: stagger(frame, i, 4),
              fps,
              config: SPRING_SMOOTH,
            });

            return (
              <React.Fragment key={node.label}>
                {/* Connecting line */}
                <div
                  style={{
                    position: 'absolute',
                    left: '50%',
                    top: '50%',
                    width: `${Math.sqrt(x * x + y * y)}px`,
                    height: 1,
                    background: `linear-gradient(90deg, ${COLORS.NEON_PURPLE}40, ${COLORS.NEON_PURPLE}15)`,
                    transformOrigin: '0 0',
                    transform: `rotate(${angle + 90}deg)`,
                    opacity: interpolate(nodeDelay, [0, 0.5], [0, 1]),
                  }}
                />
                {/* Node pill */}
                <div
                  style={{
                    position: 'absolute',
                    left: `calc(50% + ${x}px)`,
                    top: `calc(50% + ${y}px)`,
                    transform: `translate(-50%, -50%) scale(${interpolate(nodeDelay, [0, 1], [0.8, 1])})`,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '10px 20px',
                    borderRadius: 999,
                    background: isPulsing
                      ? `${COLORS.NEON_PURPLE}20`
                      : 'rgba(27,28,30,0.8)',
                    border: `1px solid ${isPulsing ? COLORS.NEON_PURPLE : 'rgba(255,255,255,0.08)'}`,
                    boxShadow: isPulsing ? glowShadow(COLORS.NEON_PURPLE, 0.5) : 'none',
                    opacity: interpolate(nodeDelay, [0, 0.3], [0, 1]),
                    transition: 'background 0.15s, border-color 0.15s',
                  }}
                >
                  <span style={{ fontSize: 20 }}>{node.icon}</span>
                  <span style={{ ...TEXT.caption, color: COLORS.TEXT_PRIMARY, fontSize: 16 }}>
                    {node.label}
                  </span>
                </div>
              </React.Fragment>
            );
          })}
        </div>

        {/* Bottom row: Waveform + Ken Burns */}
        <div
          style={{
            flexDirection: 'row',
            gap: 40,
            height: 200,
            alignItems: 'flex-end',
          }}
        >
          {/* Waveform bars */}
          <div
            style={{
              display: 'flex',
              alignItems: 'flex-end',
              gap: 3,
              height: 120,
              flex: 1,
            }}
          >
            {waveformHeights.map((h, i) => (
              <div
                key={i}
                style={{
                  flex: 1,
                  height: h,
                  background: `linear-gradient(180deg, ${COLORS.NEON_PURPLE}, ${COLORS.NEON_PURPLE}40)`,
                  borderRadius: 2,
                  minHeight: 4,
                }}
              />
            ))}
          </div>

          {/* Ken Burns demo */}
          <div
            style={{
              width: 360,
              height: 200,
              borderRadius: 12,
              overflow: 'hidden',
              border: `1px solid ${COLORS.NEON_PURPLE}40`,
              boxShadow: glowShadow(COLORS.NEON_PURPLE, 0.3),
              flexShrink: 0,
            }}
          >
            <div
              style={{
                width: '120%',
                height: '120%',
                marginLeft: `${-kbX}px`,
                background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 30%, #0f3460 60%, #533483 100%)',
                transform: `scale(${kbScale})`,
                transformOrigin: 'center center',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <span style={{ ...TEXT.overline, color: COLORS.TEXT_MUTED }}>
                KEN BURNS
              </span>
            </div>
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
