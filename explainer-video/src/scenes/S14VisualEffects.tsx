import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
  Video,
  staticFile,
} from 'remotion';
import GradientBackground from '../components/GradientBackground';
import GlassCard from '../components/GlassCard';
import {
  COLORS,
  FONT_SIZE,
  TEXT,
} from '../lib/theme';
import { SPRING_SMOOTH, stagger } from '../lib/animations';

const EFFECTS = [
  {
    name: 'Vignette',
    desc: 'Darkened edges',
    color: COLORS.VIOLET_MID,
    src: staticFile('demos/effect_vignette.mp4'),
  },
  {
    name: 'Chromatic',
    desc: 'RGB separation',
    color: COLORS.LIME,
    src: staticFile('demos/effect_chromatic.mp4'),
  },
  {
    name: 'Noise',
    desc: 'Film grain',
    color: COLORS.VIOLET_BRIGHT,
    src: staticFile('demos/effect_noise.mp4'),
  },
  {
    name: 'Glow',
    desc: 'Bloom effect',
    color: COLORS.SEAFOAM,
    src: staticFile('demos/effect_glow.mp4'),
  },
];

export const S14VisualEffects: React.FC = () => {
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
        glowY={0.5}
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
          Visual <span style={{ color: COLORS.VIOLET_BRIGHT }}>Effects</span>
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
          Professional effects for cinematic looks
        </div>

        {/* Effect cards with real demos */}
        <div
          style={{
            flex: 1,
            flexDirection: 'row',
            justifyContent: 'center',
            alignItems: 'center',
            gap: 24,
          }}
        >
          {EFFECTS.map((effect, i) => {
            const cardSpring = spring({
              frame: stagger(frame, i, 5),
              fps,
              config: SPRING_SMOOTH,
            });

            return (
              <div
                key={effect.name}
                style={{
                  width: 210,
                  opacity: interpolate(cardSpring, [0, 0.3], [0, 1]),
                  transform: `translateY(${interpolate(cardSpring, [0, 1], [25, 0])}px)`,
                }}
              >
                {/* Video preview */}
                <div
                  style={{
                    width: 210,
                    height: 140,
                    borderRadius: '10px 10px 0 0',
                    overflow: 'hidden',
                    border: `1px solid ${effect.color}20`,
                    borderBottom: 'none',
                    background: COLORS.BG_CARD,
                  }}
                >
                  <Video
                    src={effect.src}
                    style={{
                      width: '100%',
                      height: '100%',
                      objectFit: 'cover',
                    }}
                  />
                </div>
                {/* Label */}
                <div
                  style={{
                    padding: '14px 16px',
                    borderRadius: '0 0 10px 10px',
                    background: COLORS.BG_CARD,
                    border: `1px solid ${effect.color}15`,
                    borderTop: 'none',
                    textAlign: 'center',
                  }}
                >
                  <div style={{
                    ...TEXT.title,
                    fontSize: 17,
                    color: effect.color,
                    marginBottom: 3,
                  }}>
                    {effect.name}
                  </div>
                  <div style={{
                    ...TEXT.caption,
                    fontSize: 13,
                    color: COLORS.TEXT_SECONDARY,
                  }}>
                    {effect.desc}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
