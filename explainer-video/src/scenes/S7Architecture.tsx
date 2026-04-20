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
  { label: 'AI Agent', desc: 'Claude / GPT / Copilot', color: COLORS.LIME, scale: 1.2 },
  { label: 'MCP', desc: 'Protocol layer', color: COLORS.VIOLET_MID, scale: 1.0 },
  { label: 'mcp-video', desc: 'Python / FFmpeg', color: COLORS.VIOLET_BRIGHT, scale: 1.1 },
  { label: 'FFmpeg', desc: 'Encoding engine', color: COLORS.LIME, scale: 1.0 },
  { label: 'Output', desc: 'MP4 / WebM / GIF', color: COLORS.SEAFOAM, scale: 1.15 },
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
        glowColor={COLORS.LIME}
        glowX={0.3}
        glowY={0.4}
        accentTint={COLORS.VIOLET_MID}
      />

      <AbsoluteFill
        style={{
          padding: 60,
          flexDirection: 'column',
          gap: 30,
          justifyContent: 'center',
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
            width: '100%',
          }}
        >
          Architecture
        </div>

        {/* Horizontal data flow with arrows - centered */}
        <div
          style={{
            flex: 1,
            flexDirection: 'row',
            justifyContent: 'center',
            alignItems: 'center',
            gap: 16,
            width: '100%',
            maxWidth: 1200,
          }}
        >
          {LAYERS.map((layer, i) => {
            const cardSpring = spring({
              frame: stagger(frame, i, 8),
              fps,
              config: SPRING_GLASS,
            });
            const isGlowing = glowIndex === i;
            const packetProgress = (frame % 45) / 45;

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
                      width: 170,
                      padding: '16px 20px',
                      textAlign: 'center',
                      boxShadow: isGlowing ? `${glowShadow(layer.color, 0.6)}, 0 0 40px ${layer.color}30` : 'none',
                      borderColor: isGlowing ? `${layer.color}60` : undefined,
                      borderWidth: isGlowing ? 2 : 1,
                    }}
                  >
                    <div
                      style={{
                        ...TEXT.title,
                        fontSize: 18,
                        color: layer.color,
                        marginBottom: 4,
                        textShadow: isGlowing ? `0 0 10px ${layer.color}60` : 'none',
                      }}
                    >
                      {layer.label}
                    </div>
                    <div style={{ ...TEXT.caption, fontSize: 12, color: COLORS.TEXT_MUTED }}>
                      {layer.desc}
                    </div>
                  </GlassCard>
                </div>

                {i < LAYERS.length - 1 && (
                  <div style={{
                    width: 50,
                    height: 3,
                    background: `linear-gradient(90deg, ${COLORS.TEXT_MUTED}20, ${COLORS.LIME}40, ${COLORS.TEXT_MUTED}20)`,
                    position: 'relative',
                    borderRadius: 2,
                  }}>
                    {/* Animated data packet */}
                    <div
                      style={{
                        position: 'absolute',
                        top: -5,
                        left: `${packetProgress * 80 + 10}%`,
                        width: 12,
                        height: 12,
                        borderRadius: '50%',
                        background: COLORS.LIME,
                        boxShadow: `${glowShadow(COLORS.LIME, 0.8)}, 0 0 20px ${COLORS.LIME}60`,
                      }}
                    />
                    {/* Arrow head */}
                    <div style={{
                      position: 'absolute',
                      right: -6,
                      top: -4,
                      width: 0,
                      height: 0,
                      borderLeft: `8px solid ${COLORS.LIME}60`,
                      borderTop: '6px solid transparent',
                      borderBottom: '6px solid transparent',
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
