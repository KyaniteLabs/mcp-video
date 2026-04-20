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
} from '../lib/theme';
import { SPRING_SMOOTH, stagger } from '../lib/animations';

const QUALITY_SCORE = 96;
const CHECKS = [
  { name: 'Brightness', value: '128/255', icon: '☀' },
  { name: 'Contrast', value: 'High', icon: '◐' },
  { name: 'Saturation', value: '95%', icon: '🎨' },
  { name: 'Audio LUFS', value: '-16 LUFS', icon: '🔊' },
  { name: 'Color Balance', value: 'Balanced', icon: '⚖' },
];

const RING_SIZE = 110;
const RING_INNER = 88;

export const S15QualityGuardrails: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({
    frame: Math.max(0, frame - 5),
    fps,
    config: SPRING_SMOOTH,
  });

  // Score ring fill
  const scoreProgress = interpolate(frame, [20, 60], [0, QUALITY_SCORE], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.BG_DEEP }}>
      <GradientBackground
        glowColor={COLORS.LIME}
        glowX={0.5}
        glowY={0.45}
      />

      <AbsoluteFill
        style={{
          padding: 60,
          flexDirection: 'column',
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
          Quality <span style={{ color: COLORS.LIME }}>Guardrails</span>
        </div>
        <div
          style={{
            ...TEXT.subtitle,
            fontSize: 18,
            color: COLORS.TEXT_SECONDARY,
            textAlign: 'center',
            marginTop: 8,
            opacity: interpolate(titleSpring, [0.3, 0.6], [0, 1]),
          }}
        >
          Automated quality checks for every frame
        </div>

        {/* Two-column: Score ring + Check list */}
        <div
          style={{
            flex: 1,
            flexDirection: 'row',
            justifyContent: 'center',
            alignItems: 'center',
            gap: 60,
            maxWidth: 900,
            width: '100%',
          }}
        >
          {/* Left: Score ring */}
          <GlassCard
            style={{
              padding: 32,
              width: 280,
              textAlign: 'center',
              borderColor: `${COLORS.LIME}20`,
              opacity: interpolate(titleSpring, [0.2, 0.5], [0, 1]),
            }}
          >
            <div
              style={{
                width: RING_SIZE,
                height: RING_SIZE,
                borderRadius: '50%',
                background: `conic-gradient(${COLORS.LIME} 0% ${scoreProgress}%, ${COLORS.BG_ELEVATED} ${scoreProgress}% 100%)`,
                margin: '0 auto 16px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <div
                style={{
                  width: RING_INNER,
                  height: RING_INNER,
                  borderRadius: '50%',
                  background: COLORS.BG_CARD,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <span style={{
                  ...TEXT.display,
                  fontSize: 30,
                  color: COLORS.LIME,
                }}>
                  {Math.round(scoreProgress)}
                </span>
              </div>
            </div>
            <div style={{
              ...TEXT.title,
              fontSize: 18,
              color: COLORS.TEXT_PRIMARY,
              marginBottom: 4,
            }}>
              Quality Score
            </div>
            <div style={{
              ...TEXT.caption,
              fontSize: 13,
              color: COLORS.TEXT_SECONDARY,
            }}>
              All checks passing
            </div>
          </GlassCard>

          {/* Right: Check list */}
          <div style={{
            flexDirection: 'column',
            gap: 12,
            width: 340,
          }}>
            {CHECKS.map((check, i) => {
              const checkSpring = spring({
                frame: stagger(frame, i, 5),
                fps,
                config: SPRING_SMOOTH,
              });

              return (
                <GlassCard
                  key={check.name}
                  style={{
                    padding: '14px 18px',
                    flexDirection: 'row',
                    alignItems: 'center',
                    gap: 14,
                    opacity: interpolate(checkSpring, [0, 0.3], [0, 1]),
                    transform: `translateX(${interpolate(checkSpring, [0, 1], [20, 0])}px)`,
                    borderColor: `${COLORS.LIME}15`,
                  }}
                >
                  <span style={{ fontSize: 22 }}>{check.icon}</span>
                  <div style={{ flex: 1 }}>
                    <div style={{
                      ...TEXT.body,
                      fontSize: 15,
                      color: COLORS.TEXT_PRIMARY,
                      fontWeight: 500,
                    }}>
                      {check.name}
                    </div>
                    <div style={{
                      ...TEXT.caption,
                      fontSize: 12,
                      color: COLORS.TEXT_MUTED,
                    }}>
                      {check.value}
                    </div>
                  </div>
                  <div
                    style={{
                      width: 22,
                      height: 22,
                      borderRadius: '50%',
                      background: COLORS.LIME,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      opacity: interpolate(checkSpring, [0.3, 0.6], [0, 1]),
                      transform: `scale(${interpolate(checkSpring, [0.3, 1], [0, 1])})`,
                    }}
                  >
                    <span style={{ color: COLORS.BG_DEEP, fontSize: 12, fontWeight: 700 }}>✓</span>
                  </div>
                </GlassCard>
              );
            })}
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
