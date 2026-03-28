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

            return (
              <div
                key={feature.label}
                style={{
                  opacity: interpolate(cardSpring, [0, 0.3], [0, 1]),
                  transform: `scale(${interpolate(cardSpring, [0, 1], [0.92, 1])}) rotate(${rotate}deg)`,
                }}
              >
                <GlassCard
                  accentColor={COLORS.NEON_PURPLE}
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

        {/* Right: Before/after color grading slider */}
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
              position: 'relative',
              borderRadius: 12,
              overflow: 'hidden',
              border: '1px solid rgba(255,255,255,0.08)',
            }}
          >
            {/* Before side */}
            <div
              style={{
                width: '100%',
                height: 400,
                background: 'linear-gradient(135deg, #2d1b3d, #1a1a2e, #16213e)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <span style={{ ...TEXT.overline, color: COLORS.TEXT_MUTED, fontSize: 14 }}>
                BEFORE
              </span>
            </div>
            {/* After overlay with moving divider */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                right: 0,
                width: `${interpolate(Math.sin(frame * 0.02), [-1, 1], [35, 65])}%`,
                height: '100%',
                background: 'linear-gradient(135deg, #0f3460, #533483, #e94560)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: '0 12px 12px 0',
              }}
            >
              <span style={{ ...TEXT.overline, color: '#fff', fontSize: 14 }}>
                AFTER
              </span>
            </div>
            {/* Divider line */}
            <div
              style={{
                position: 'absolute',
                top: 0,
                left: `${interpolate(Math.sin(frame * 0.02), [-1, 1], [35, 65])}%`,
                height: '100%',
                width: 3,
                background: COLORS.NEON_PURPLE,
                boxShadow: glowShadow(COLORS.NEON_PURPLE),
              }}
            />
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
