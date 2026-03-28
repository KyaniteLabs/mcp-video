import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from 'remotion';
import GradientBackground from '../components/GradientBackground';
import GlassCard from '../components/GlassCard';
import {
  COLORS,
  FONT_SIZE,
  TEXT,
  glowShadow,
} from '../lib/theme';
import { SPRING_GLASS, stagger, useAmbientMotion } from '../lib/animations';

const LAYERS = [
  { label: 'AI Agent', desc: 'Claude / GPT / Copilot', color: COLORS.NEON_CYAN },
  { label: 'MCP', desc: 'Protocol layer', color: COLORS.NEON_PURPLE },
  { label: 'mcp-video', desc: 'Python / FFmpeg', color: COLORS.NEON_MAGENTA },
  { label: 'FFmpeg', desc: 'Encoding engine', color: COLORS.NEON_GREEN },
  { label: 'Output', desc: 'MP4 / WebM / GIF', color: COLORS.NEON_ORANGE },
];

export const S7Architecture: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { shimmer } = useAmbientMotion(frame);

  // Hover glow cycle
  const glowIndex = Math.floor(frame / 40) % LAYERS.length;

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.BG_DEEP }}>
      <GradientBackground
        glowColor={COLORS.NEON_CYAN}
        glowX={0.3}
        glowY={0.4}
        accentTint={COLORS.NEON_MAGENTA}
      />

      <AbsoluteFill
        style={{
          padding: 60,
          flexDirection: 'column',
          gap: 30,
        }}
      >
        {/* Title */}
        <div
          style={{
            ...TEXT.headline,
            fontSize: FONT_SIZE.HEADLINE,
            color: COLORS.TEXT_PRIMARY,
            textAlign: 'center',
          }}
        >
          Architecture
        </div>

        {/* Horizontal data flow */}
        <div
          style={{
            flex: 1,
            justifyContent: 'center',
            alignItems: 'center',
            gap: 20,
          }}
        >
          {LAYERS.map((layer, i) => {
            const cardSpring = spring({
              frame: stagger(frame, i, 8),
              fps,
              config: SPRING_GLASS,
            });
            const isGlowing = glowIndex === i;
            const packetProgress = (frame % 60) / 60;

            return (
              <React.Fragment key={layer.label}>
                <div
                  style={{
                    opacity: interpolate(cardSpring, [0, 0.3], [0, 1]),
                    transform: `translateY(${interpolate(cardSpring, [0, 1], [20, 0])}px)`,
                  }}
                >
                  <GlassCard
                    accentColor={layer.color}
                    accentTop
                    style={{
                      width: 200,
                      padding: '16px 20px',
                      textAlign: 'center',
                      boxShadow: isGlowing ? glowShadow(layer.color, 0.5) : 'none',
                      borderColor: isGlowing ? `${layer.color}40` : undefined,
                    }}
                  >
                    <div
                      style={{
                        ...TEXT.title,
                        fontSize: 18,
                        color: layer.color,
                        marginBottom: 4,
                      }}
                    >
                      {layer.label}
                    </div>
                    <div style={{ ...TEXT.caption, fontSize: 13, color: COLORS.TEXT_MUTED }}>
                      {layer.desc}
                    </div>
                  </GlassCard>
                </div>

                {i < LAYERS.length - 1 && (
                  <div style={{
                    width: 60,
                    height: 2,
                    background: `${COLORS.TEXT_MUTED}15`,
                    position: 'relative',
                  }}>
                    <div
                      style={{
                        position: 'absolute',
                        top: -4,
                        left: `${packetProgress * 100}%`,
                        width: 10,
                        height: 10,
                        borderRadius: '50%',
                        background: COLORS.NEON_CYAN,
                        boxShadow: glowShadow(COLORS.NEON_CYAN, 0.5),
                      }}
                    />
                    <div style={{
                      position: 'absolute',
                      right: -4,
                      top: -3,
                      width: 0,
                      height: 0,
                      borderLeft: `6px solid ${COLORS.TEXT_MUTED}25`,
                      borderTop: '5px solid transparent',
                      borderBottom: '5px solid transparent',
                    }} />
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
