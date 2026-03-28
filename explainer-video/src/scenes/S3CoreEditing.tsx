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
  FONT_DISPLAY,
  TEXT,
  glowShadow,
} from '../lib/theme';
import { SPRING_GLASS, stagger } from '../lib/animations';

const FEATURES = [
  { icon: '✂️', label: 'Trim & Cut', desc: 'Precision frame control' },
  { icon: '🔗', label: 'Merge', desc: 'Multi-clip composition' },
  { icon: '🎨', label: 'Color Grade', desc: 'Cinematic presets' },
  { icon: '🔊', label: 'Audio Sync', desc: 'Smart normalization' },
  { icon: '📐', label: 'Resize', desc: 'Any aspect ratio' },
  { icon: '⚡', label: 'Convert', desc: 'Format flexibility' },
];

export const S3CoreEditing: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.BG_DEEP }}>
      <GradientBackground
        glowColor={COLORS.NEON_PURPLE}
        glowX={0.35}
        glowY={0.5}
      />

      <AbsoluteFill
        style={{
          flexDirection: 'row',
          padding: 80,
          gap: 60,
        }}
      >
        {/* Left: Feature grid (3x2) */}
        <div
          style={{
            flex: 1,
            display: 'grid',
            gridTemplateColumns: '1fr 1fr 1fr',
            gridTemplateRows: '1fr 1fr',
            gap: 16,
            alignContent: 'center',
          }}
        >
          {FEATURES.map((feature, i) => {
            const cardSpring = spring({
              frame: stagger(frame, i, 6),
              fps,
              config: SPRING_GLASS,
            });
            const rotate = interpolate(cardSpring, [0, 1], [2, 0]);
            const demoIndex = Math.floor((frame % 210) / 70);
            const isActive = i === demoIndex;

            return (
              <div
                key={feature.label}
                style={{
                  opacity: interpolate(cardSpring, [0, 0.3], [0, 1]),
                  transform: `scale(${interpolate(cardSpring, [0, 1], [0.92, 1])}) rotate(${rotate}deg)`,
                }}
              >
                <GlassCard
                  accentColor={isActive ? COLORS.NEON_CYAN : COLORS.NEON_PURPLE}
                  accentTop
                  shimmer
                  style={{ padding: '20px 16px' }}
                >
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 28, marginBottom: 8 }}>{feature.icon}</div>
                    <div
                      style={{
                        ...TEXT.title,
                        fontSize: 18,
                        color: COLORS.TEXT_PRIMARY,
                        marginBottom: 4,
                      }}
                    >
                      {feature.label}
                    </div>
                    <div
                      style={{
                        ...TEXT.caption,
                        fontSize: 14,
                        color: COLORS.TEXT_MUTED,
                      }}
                    >
                      {feature.desc}
                    </div>
                  </div>
                </GlassCard>
              </div>
            );
          })}
        </div>

        {/* Right: Cycling demo panel */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <div
            style={{
              width: '100%',
              maxWidth: 500,
              borderRadius: 12,
              overflow: 'hidden',
              border: '1px solid rgba(255,255,255,0.08)',
              background: 'rgba(0,0,0,0.3)',
              padding: 24,
            }}
          >
            <div style={{ ...TEXT.overline, color: COLORS.NEON_PURPLE, fontSize: 13, marginBottom: 20 }}>
              DEMO
            </div>

            {(() => {
              const cycleFrame = frame % 210;
              const demoIdx = Math.floor(cycleFrame / 70);

              const demos = [
                {
                  title: 'Trim & Cut',
                  desc: 'Precision frame selection',
                  icon: '✂️',
                  visual: (
                    <div style={{ position: 'relative', height: 200 }}>
                      <div style={{
                        position: 'absolute', top: '50%', left: 0, right: 0,
                        height: 40, transform: 'translateY(-50%)',
                        background: 'rgba(255,255,255,0.06)', borderRadius: 8,
                      }}>
                        <div style={{
                          position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
                          background: 'rgba(255,255,255,0.04)', borderRadius: 8,
                        }} />
                        <div style={{
                          position: 'absolute', top: 0,
                          left: `${interpolate(cycleFrame, [0, 70], [10, 60], { extrapolateRight: 'clamp' })}%`,
                          width: '30%', height: '100%',
                          background: COLORS.NEON_PURPLE, borderRadius: 8,
                          boxShadow: glowShadow(COLORS.NEON_PURPLE, 0.4),
                        }} />
                        <div style={{
                          position: 'absolute',
                          left: `${interpolate(cycleFrame, [0, 70], [10, 60], { extrapolateRight: 'clamp' })}%`,
                          top: -16, fontSize: 24, transform: 'translateX(-50%)',
                        }}>✂️</div>
                      </div>
                    </div>
                  ),
                },
                {
                  title: 'Color Grade',
                  desc: 'Cinematic presets',
                  icon: '🎨',
                  visual: (
                    <div style={{ height: 200, position: 'relative', borderRadius: 8, overflow: 'hidden' }}>
                      <div style={{
                        position: 'absolute', inset: 0,
                        background: 'linear-gradient(135deg, #3a3a3a, #4a4a4a, #3a3a3a)',
                      }} />
                      <div style={{
                        position: 'absolute', inset: 0,
                        background: 'linear-gradient(135deg, #0f3460, #533483, #e94560)',
                        clipPath: `inset(0 ${100 - interpolate(cycleFrame, [0, 70], [0, 100], { extrapolateRight: 'clamp' })}% 0 0)`,
                      }} />
                    </div>
                  ),
                },
                {
                  title: 'Merge',
                  desc: 'Multi-clip composition',
                  icon: '🔗',
                  visual: (
                    <div style={{ height: 200, display: 'flex', gap: 8, alignItems: 'center' }}>
                      <div style={{
                        flex: 1, height: 180, borderRadius: 8,
                        background: 'linear-gradient(135deg, #1a1a2e, #16213e)',
                        border: '1px solid rgba(255,255,255,0.06)',
                        opacity: interpolate(cycleFrame, [0, 70], [0.5, 1], { extrapolateRight: 'clamp' }),
                      }} />
                      <div style={{
                        flex: 1, height: 180, borderRadius: 8,
                        background: 'linear-gradient(135deg, #2d1b3d, #0f3460)',
                        border: '1px solid rgba(255,255,255,0.06)',
                        transform: `translateX(${interpolate(cycleFrame, [0, 70], [200, 0], { extrapolateRight: 'clamp' })}px)`,
                      }} />
                    </div>
                  ),
                },
              ];

              const demo = demos[demoIdx];
              const demoProgress = spring({
                frame: Math.max(0, frame - demoIdx * 70),
                fps,
                config: { damping: 25, stiffness: 80, mass: 0.8 },
              });

              return (
                <div key={demo.title} style={{
                  opacity: interpolate(demoProgress, [0, 0.3], [0, 1]),
                  transform: `translateY(${interpolate(demoProgress, [0, 1], [10, 0])}px)`,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                    <span style={{ fontSize: 28 }}>{demo.icon}</span>
                    <div>
                      <div style={{ ...TEXT.title, fontSize: 20, color: COLORS.TEXT_PRIMARY }}>{demo.title}</div>
                      <div style={{ ...TEXT.caption, fontSize: 14, color: COLORS.TEXT_MUTED }}>{demo.desc}</div>
                    </div>
                  </div>
                  {demo.visual}
                </div>
              );
            })()}
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
