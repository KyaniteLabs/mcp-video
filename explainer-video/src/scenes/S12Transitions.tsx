import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, Easing } from 'remotion';
import GlassCard from '../components/GlassCard';
import { COLORS, TEXT, FONT_SIZE, glowShadow } from '../lib/theme';

// Transitions Scene for v1.0
export const S12Transitions: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  const progress = frame / (fps * 5); // 5 seconds for this scene
  
  // Entrance animations
  const titleOpacity = interpolate(progress, [0, 0.15], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  
  const titleY = interpolate(progress, [0, 0.15], [30, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  
  // Card animations
  const cardDelay = 0.12;
  const getCardProgress = (index: number) => 
    interpolate(progress, [0.2 + cardDelay * index, 0.35 + cardDelay * index], [0, 1], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
      easing: Easing.out(Easing.cubic),
    });
  
  const transitions = [
    {
      name: 'Glitch',
      desc: 'RGB shift + noise',
      icon: '⚡',
      color: COLORS.LIME,
      preview: 'RGB SPLIT',
    },
    {
      name: 'Pixelate',
      desc: 'Block dissolve',
      icon: '🔲',
      color: COLORS.VIOLET_BRIGHT,
      preview: 'PIXEL\nBLOCKS',
    },
    {
      name: 'Morph',
      desc: 'Mesh warp',
      icon: '🔮',
      color: COLORS.CYAN_BRIGHT,
      preview: 'WARP',
    },
  ];
  
  return (
    <AbsoluteFill style={{ background: COLORS.BG_DEEP }}>
      {/* Background accent */}
      <div
        style={{
          position: 'absolute',
          width: 800,
          height: 400,
          background: `linear-gradient(90deg, ${COLORS.LIME}10, ${COLORS.VIOLET_MID}10)`,
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%) rotate(-5deg)',
          filter: 'blur(60px)',
        }}
      />
      
      {/* Header */}
      <div
        style={{
          position: 'absolute',
          top: 100,
          left: 0,
          right: 0,
          textAlign: 'center',
          opacity: titleOpacity,
          transform: `translateY(${titleY}px)`,
        }}
      >
        <div
          style={{
            ...TEXT.overline,
            fontSize: FONT_SIZE.OVERLINE,
            color: COLORS.LIME,
            marginBottom: 16,
          }}
        >
          v1.0 FEATURES
        </div>
        <h2
          style={{
            ...TEXT.headline,
            fontSize: FONT_SIZE.HEADLINE,
            color: COLORS.TEXT_PRIMARY,
            margin: 0,
          }}
        >
          Video Transitions
        </h2>
        <p
          style={{
            ...TEXT.body,
            fontSize: FONT_SIZE.SUBTITLE,
            color: COLORS.TEXT_SECONDARY,
            marginTop: 12,
          }}
        >
          Professional transitions for seamless clip connections
        </p>
      </div>
      
      {/* Transition Cards */}
      <div
        style={{
          position: 'absolute',
          top: 320,
          left: '50%',
          transform: 'translateX(-50%)',
          display: 'flex',
          gap: 40,
        }}
      >
        {transitions.map((t, i) => {
          const p = getCardProgress(i);
          const floatY = interpolate(
            frame,
            [0, fps * 2],
            [0, -10],
            { extrapolateRight: 'extend' }
          );
          
          return (
            <GlassCard
              key={t.name}
              style={{
                width: 280,
                height: 320,
                padding: 0,
                overflow: 'hidden',
                opacity: p,
                transform: `translateY(${(1 - p) * 40}px) translateY(${floatY * (i % 2 === 0 ? 1 : -1)}px)`,
                borderColor: `${t.color}40`,
                boxShadow: glowShadow(t.color, 0.5),
              }}
            >
              {/* Preview area */}
              <div
                style={{
                  height: 160,
                  background: `linear-gradient(135deg, ${t.color}20, ${COLORS.BG_CARD})`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  borderBottom: `1px solid ${t.color}30`,
                }}
              >
                <span
                  style={{
                    fontSize: 64,
                    filter: `drop-shadow(0 0 20px ${t.color}50)`,
                  }}
                >
                  {t.icon}
                </span>
              </div>
              
              {/* Info area */}
              <div style={{ padding: 24, textAlign: 'center' }}>
                <h3
                  style={{
                    ...TEXT.title,
                    fontSize: 28,
                    color: t.color,
                    margin: '0 0 8px 0',
                  }}
                >
                  {t.name}
                </h3>
                <p
                  style={{
                    ...TEXT.body,
                    fontSize: 16,
                    color: COLORS.TEXT_SECONDARY,
                    margin: 0,
                  }}
                >
                  {t.desc}
                </p>
              </div>
            </GlassCard>
          );
        })}
      </div>
      
    </AbsoluteFill>
  );
};
