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
import { SPRING_SMOOTH, stagger } from '../lib/animations';

const AI_FEATURES = [
  { icon: '🎤', title: 'Silence Removal', desc: 'Auto-remove dead air', color: COLORS.LIME },
  { icon: '📝', title: 'Transcription', desc: 'Whisper-powered STT', color: COLORS.SEAFOAM },
  { icon: '🎬', title: 'Scene Detection', desc: 'ML-enhanced cuts', color: COLORS.SEAFOAM },
  { icon: '🎵', title: 'Stem Separation', desc: 'Isolate vocals, drums', color: COLORS.VIOLET_MID },
  { icon: '🔍', title: 'AI Upscale', desc: 'Super-resolution 2x/4x', color: COLORS.LIME },
  { icon: '🎨', title: 'Color Grading', desc: 'Auto color correction', color: COLORS.VIOLET_BRIGHT },
  { icon: '🔊', title: 'Spatial Audio', desc: '3D audio positioning', color: COLORS.VIOLET_MID },
];

export const S11AIFeatures: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({
    frame: Math.max(0, frame - 5),
    fps,
    config: SPRING_SMOOTH,
  });

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.BG_DEEP }}>
      <GradientBackground
        glowColor={COLORS.VIOLET_MID}
        glowX={0.5}
        glowY={0.4}
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
          <span style={{ color: COLORS.VIOLET_BRIGHT }}>AI</span>-Powered Editing
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
          7 intelligent features for automated processing
        </div>

        {/* Feature grid — 4 top + 3 bottom centered */}
        <div
          style={{
            flex: 1,
            justifyContent: 'center',
            alignItems: 'center',
          }}
        >
          {/* Top row: 4 cards */}
          <div style={{
            flexDirection: 'row',
            gap: 20,
            justifyContent: 'center',
            marginBottom: 20,
          }}>
            {AI_FEATURES.slice(0, 4).map((feature, i) => {
              const cardSpring = spring({
                frame: stagger(frame, i, 5),
                fps,
                config: SPRING_SMOOTH,
              });
              return (
                <GlassCard
                  key={feature.title}
                  style={{
                    width: 200,
                    padding: '20px 16px',
                    textAlign: 'center',
                    opacity: interpolate(cardSpring, [0, 0.3], [0, 1]),
                    transform: `translateY(${interpolate(cardSpring, [0, 1], [20, 0])}px)`,
                    borderColor: `${feature.color}20`,
                  }}
                >
                  <div style={{ fontSize: 32, marginBottom: 8 }}>{feature.icon}</div>
                  <div style={{
                    ...TEXT.title,
                    fontSize: 16,
                    color: COLORS.TEXT_PRIMARY,
                    marginBottom: 4,
                  }}>
                    {feature.title}
                  </div>
                  <div style={{
                    ...TEXT.caption,
                    fontSize: 13,
                    color: COLORS.TEXT_SECONDARY,
                  }}>
                    {feature.desc}
                  </div>
                </GlassCard>
              );
            })}
          </div>

          {/* Bottom row: 3 cards centered */}
          <div style={{
            flexDirection: 'row',
            gap: 20,
            justifyContent: 'center',
          }}>
            {AI_FEATURES.slice(4).map((feature, i) => {
              const cardSpring = spring({
                frame: stagger(frame, i + 4, 5),
                fps,
                config: SPRING_SMOOTH,
              });
              return (
                <GlassCard
                  key={feature.title}
                  style={{
                    width: 200,
                    padding: '20px 16px',
                    textAlign: 'center',
                    opacity: interpolate(cardSpring, [0, 0.3], [0, 1]),
                    transform: `translateY(${interpolate(cardSpring, [0, 1], [20, 0])}px)`,
                    borderColor: `${feature.color}20`,
                  }}
                >
                  <div style={{ fontSize: 32, marginBottom: 8 }}>{feature.icon}</div>
                  <div style={{
                    ...TEXT.title,
                    fontSize: 16,
                    color: COLORS.TEXT_PRIMARY,
                    marginBottom: 4,
                  }}>
                    {feature.title}
                  </div>
                  <div style={{
                    ...TEXT.caption,
                    fontSize: 13,
                    color: COLORS.TEXT_SECONDARY,
                  }}>
                    {feature.desc}
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
