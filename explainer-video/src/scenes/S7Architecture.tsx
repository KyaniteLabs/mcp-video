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
  FONT_MONO,
  TEXT,
  glowShadow,
} from '../lib/theme';
import { SPRING_GLASS, stagger, useAmbientMotion } from '../lib/animations';

const LAYERS = [
  {
    label: 'AI Agent',
    desc: 'Claude / GPT / Copilot',
    code: 'agent.send(tool_call)',
    color: COLORS.NEON_CYAN,
  },
  {
    label: 'MCP Protocol',
    desc: 'JSON-RPC over stdio',
    code: '{"method": "tools/call"}',
    color: COLORS.NEON_PURPLE,
  },
  {
    label: 'mcp-video Server',
    desc: 'Python / FFmpeg bridge',
    code: 'video.trim(start=0, end=30)',
    color: COLORS.NEON_MAGENTA,
  },
  {
    label: 'FFmpeg',
    desc: 'Industry-grade encoding',
    code: '$ ffmpeg -i input.mp4 ...',
    color: COLORS.NEON_GREEN,
  },
  {
    label: 'Output',
    desc: 'MP4 / WebM / GIF',
    code: 'out/video-final.mp4',
    color: COLORS.NEON_ORANGE,
  },
];

const DATA_FLOW = ['MCP Client', 'JSON-RPC', 'Server', 'FFmpeg', 'Output'];

export const S7Architecture: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { shimmer } = useAmbientMotion(frame);

  // Hover glow cycle
  const glowIndex = Math.floor(frame / 40) % LAYERS.length;

  // Arrow traveling dot
  const arrowProgress = (frame % 60) / 60;

  // Data flow dot
  const flowProgress = (frame % 90) / 90;

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

        {/* Layer stack */}
        <div
          style={{
            flex: 1,
            justifyContent: 'center',
            alignItems: 'center',
            gap: 12,
          }}
        >
          {LAYERS.map((layer, i) => {
            const cardSpring = spring({
              frame: stagger(frame, i, 5),
              fps,
              config: SPRING_GLASS,
            });
            const isGlowing = glowIndex === i;

            return (
              <React.Fragment key={layer.label}>
                <div
                  style={{
                    opacity: interpolate(cardSpring, [0, 0.3], [0, 1]),
                    transform: `translateX(${interpolate(cardSpring, [0, 1], [-40, 0])}px)`,
                  }}
                >
                  <GlassCard
                    accentColor={layer.color}
                    accentTop
                    style={{
                      width: 440,
                      padding: '16px 24px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      boxShadow: isGlowing ? glowShadow(layer.color, 0.4) : 'none',
                    }}
                  >
                    <div>
                      <div
                        style={{
                          ...TEXT.title,
                          fontSize: 18,
                          color: layer.color,
                          marginBottom: 2,
                        }}
                      >
                        {layer.label}
                      </div>
                      <div style={{ ...TEXT.caption, fontSize: 13, color: COLORS.TEXT_MUTED }}>
                        {layer.desc}
                      </div>
                    </div>
                    <div
                      style={{
                        fontFamily: FONT_MONO,
                        fontSize: 14,
                        color: COLORS.TEXT_MUTED,
                        background: 'rgba(0,0,0,0.3)',
                        padding: '4px 10px',
                        borderRadius: 6,
                      }}
                    >
                      {layer.code}
                    </div>
                  </GlassCard>
                </div>

                {/* Arrow between layers */}
                {i < LAYERS.length - 1 && (
                  <div style={{ position: 'relative', height: 20 }}>
                    <div
                      style={{
                        width: 2,
                        height: 20,
                        background: `${COLORS.TEXT_MUTED}20`,
                        margin: '0 auto',
                      }}
                    >
                      <div
                        style={{
                          width: 8,
                          height: 8,
                          borderRadius: '50%',
                          background: COLORS.NEON_CYAN,
                          position: 'absolute',
                          top: `${arrowProgress * 100}%`,
                          left: '50%',
                          transform: 'translate(-50%, -50%)',
                          boxShadow: glowShadow(COLORS.NEON_CYAN, 0.4),
                        }}
                      />
                    </div>
                    <div
                      style={{
                        width: 0,
                        height: 0,
                        borderLeft: '5px solid transparent',
                        borderRight: '5px solid transparent',
                        borderTop: `6px solid ${COLORS.TEXT_MUTED}30`,
                        position: 'absolute',
                        bottom: 0,
                        left: '50%',
                        transform: 'translateX(-50%)',
                      }}
                    />
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* Horizontal data flow pipeline */}
        <div
          style={{
            flexDirection: 'row',
            gap: 0,
            alignSelf: 'center',
            alignItems: 'center',
            marginBottom: 20,
          }}
        >
          {DATA_FLOW.map((stage, i) => (
            <React.Fragment key={stage}>
              <div
                style={{
                  padding: '6px 16px',
                  borderRadius: 8,
                  background: 'rgba(27,28,30,0.7)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  ...TEXT.caption,
                  fontSize: 12,
                  color: COLORS.TEXT_SECONDARY,
                }}
              >
                {stage}
              </div>
              {i < DATA_FLOW.length - 1 && (
                <div style={{ width: 40, height: 2, background: 'rgba(255,255,255,0.06)', position: 'relative' }}>
                  <div
                    style={{
                      position: 'absolute',
                      top: -3,
                      left: `${flowProgress * 100}%`,
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      background: COLORS.NEON_CYAN,
                      boxShadow: glowShadow(COLORS.NEON_CYAN, 0.3),
                    }}
                  />
                </div>
              )}
            </React.Fragment>
          ))}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
