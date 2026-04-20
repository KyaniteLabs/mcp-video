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
import {
  COLORS,
  FONT_SIZE,
  TEXT,
} from '../lib/theme';
import { SPRING_SMOOTH, stagger } from '../lib/animations';

const TRANSITIONS = [
  {
    name: 'Glitch',
    desc: 'RGB shift + noise',
    color: COLORS.LIME,
    src: staticFile('demos/trans_glitch.mp4'),
  },
  {
    name: 'Pixelate',
    desc: 'Block dissolve',
    color: COLORS.VIOLET_BRIGHT,
    src: staticFile('demos/trans_pixelate.mp4'),
  },
  {
    name: 'Morph',
    desc: 'Mesh warp',
    color: COLORS.SEAFOAM,
    src: staticFile('demos/trans_morph.mp4'),
  },
];

export const S12Transitions: React.FC = () => {
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
        glowColor={COLORS.LIME}
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
          Video <span style={{ color: COLORS.LIME }}>Transitions</span>
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
          Professional transitions for seamless clip connections
        </div>

        {/* Transition demo cards */}
        <div
          style={{
            flex: 1,
            flexDirection: 'row',
            justifyContent: 'center',
            alignItems: 'center',
            gap: 32,
          }}
        >
          {TRANSITIONS.map((t, i) => {
            const cardSpring = spring({
              frame: stagger(frame, i, 6),
              fps,
              config: SPRING_SMOOTH,
            });

            return (
              <div
                key={t.name}
                style={{
                  width: 300,
                  opacity: interpolate(cardSpring, [0, 0.3], [0, 1]),
                  transform: `translateY(${interpolate(cardSpring, [0, 1], [30, 0])}px)`,
                }}
              >
                {/* Video preview */}
                <div
                  style={{
                    width: 300,
                    height: 180,
                    borderRadius: '12px 12px 0 0',
                    overflow: 'hidden',
                    border: `1px solid ${t.color}30`,
                    borderBottom: 'none',
                    background: COLORS.BG_CARD,
                  }}
                >
                  <Video
                    src={t.src}
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
                    padding: '16px 20px',
                    borderRadius: '0 0 12px 12px',
                    background: COLORS.BG_CARD,
                    border: `1px solid ${t.color}20`,
                    borderTop: 'none',
                    textAlign: 'center',
                  }}
                >
                  <div style={{
                    ...TEXT.title,
                    fontSize: 20,
                    color: t.color,
                    marginBottom: 4,
                  }}>
                    {t.name}
                  </div>
                  <div style={{
                    ...TEXT.caption,
                    fontSize: 14,
                    color: COLORS.TEXT_SECONDARY,
                  }}>
                    {t.desc}
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
