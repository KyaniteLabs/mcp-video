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
  GRADIENT_PRIMARY,
  FONT_SIZE,
  FONT_DISPLAY,
  TEXT,
  glowShadow,
} from '../lib/theme';
import { SPRING_SMOOTH } from '../lib/animations';

export const S8MCPPrimer: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const mcpSpring = spring({ frame, fps, config: SPRING_SMOOTH });

  const eqOpacity = interpolate(frame, [20, 30], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const descOpacity = interpolate(frame, [25, 40], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const visualOpacity = interpolate(frame, [40, 55], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const pulseScale = interpolate(
    Math.sin(frame * 0.08),
    [-1, 1],
    [0.98, 1.02],
  );

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.BG_DEEP }}>
      <GradientBackground
        glowColor={COLORS.LIME}
        glowX={0.5}
        glowY={0.4}
      />

      <AbsoluteFill
        style={{
          justifyContent: 'center',
          alignItems: 'center',
          flexDirection: 'row',
          gap: 80,
        }}
      >
        {/* Left: MCP letters */}
        <div
          style={{
            opacity: interpolate(mcpSpring, [0, 0.3], [0, 1]),
            transform: `scale(${interpolate(mcpSpring, [0, 1], [0.9, 1])})`,
          }}
        >
          <span
            style={{
              ...TEXT.display,
              fontSize: FONT_SIZE.HEADLINE,
              background: GRADIENT_PRIMARY,
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            MCP
          </span>
        </div>

        {/* Center: Equals + description */}
        <div
          style={{
            flexDirection: 'column',
            alignItems: 'center',
            gap: 16,
          }}
        >
          <span style={{
            ...TEXT.display,
            fontSize: 72,
            color: COLORS.TEXT_MUTED,
            opacity: eqOpacity,
          }}>
            =
          </span>
          <div
            style={{
              ...TEXT.subtitle,
              fontSize: 28,
              color: COLORS.LIME,
              textAlign: 'center',
              opacity: descOpacity,
            }}
          >
            USB-C for AI tools
          </div>
          <div
            style={{
              ...TEXT.body,
              fontSize: 18,
              color: COLORS.TEXT_MUTED,
              textAlign: 'center',
              maxWidth: 300,
              opacity: descOpacity,
            }}
          >
            Universal standard for connecting AI models to tools
          </div>
        </div>

        {/* Right: Visual analogy */}
        <div
          style={{
            opacity: visualOpacity,
            transform: `scale(${interpolate(visualOpacity, [0, 1], [0.9, 1]) * pulseScale})`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <div style={{
            width: 48,
            height: 48,
            borderRadius: 10,
            border: `2px solid ${COLORS.LIME}50`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <span style={{ fontSize: 24 }}>🤖</span>
          </div>
          <div style={{
            width: 3,
            height: 40,
            background: `linear-gradient(180deg, ${COLORS.LIME}60, ${COLORS.LIME}20)`,
            borderRadius: 2,
          }} />
          <div style={{
            width: 48,
            height: 48,
            borderRadius: 10,
            border: `2px solid ${COLORS.VIOLET_MID}50`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: glowShadow(COLORS.VIOLET_MID, 0.3),
          }}>
            <span style={{ fontSize: 24 }}>💻</span>
          </div>
          <div style={{
            width: 48,
            height: 48,
            borderRadius: 10,
            border: `2px solid ${COLORS.VIOLET_BRIGHT}50`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <span style={{ fontSize: 24 }}>🔧</span>
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
