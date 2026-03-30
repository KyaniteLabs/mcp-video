import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, Easing, Video, staticFile } from 'remotion';
import GlassCard from '../components/GlassCard';
import { COLORS, TEXT, FONT_SIZE, glowShadow } from '../lib/theme';

// Visual Effects Scene for v1.0 - Now with REAL demo videos
export const S14VisualEffects: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  const progress = frame / (fps * 5);
  
  // Entrance animations
  const titleOpacity = interpolate(progress, [0, 0.15], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  
  const gridOpacity = interpolate(progress, [0.2, 0.35], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  
  // Real effect demo videos
  const effects = [
    { 
      name: 'Vignette', 
      desc: 'Darkened edges', 
      icon: '◐', 
      color: COLORS.VIOLET_MID,
      demo: 'demos/effect_vignette.mp4'
    },
    { 
      name: 'Chromatic', 
      desc: 'RGB separation', 
      icon: '⚡', 
      color: COLORS.LIME,
      demo: 'demos/effect_chromatic.mp4'
    },
    { 
      name: 'Scanlines', 
      desc: 'CRT overlay', 
      icon: '☰', 
      color: COLORS.CYAN_BRIGHT,
      demo: 'demos/effect_source.mp4'  // Fallback - scanlines has filter issue
    },
    { 
      name: 'Noise', 
      desc: 'Film grain', 
      icon: '✻', 
      color: COLORS.TEXT_MUTED,
      demo: 'demos/effect_noise.mp4'
    },
    { 
      name: 'Glow', 
      desc: 'Bloom effect', 
      icon: '✦', 
      color: COLORS.VIOLET_BRIGHT,
      demo: 'demos/effect_glow.mp4'
    },
  ];
  
  return (
    <AbsoluteFill style={{ background: COLORS.BG_DEEP }}>
      {/* Background gradient */}
      <div
        style={{
          position: 'absolute',
          width: 600,
          height: 600,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${COLORS.VIOLET_MID}15 0%, transparent 70%)`,
          top: '30%',
          right: '-10%',
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
        }}
      >
        <div
          style={{
            ...TEXT.overline,
            fontSize: FONT_SIZE.OVERLINE,
            color: COLORS.VIOLET_BRIGHT,
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
          Visual Effects
        </h2>
        <p
          style={{
            ...TEXT.body,
            fontSize: FONT_SIZE.SUBTITLE,
            color: COLORS.TEXT_SECONDARY,
            marginTop: 12,
          }}
        >
          Professional effects for cinematic looks
        </p>
      </div>
      
      {/* Effects Grid with Real Videos */}
      <div
        style={{
          position: 'absolute',
          top: 280,
          left: '50%',
          transform: 'translateX(-50%)',
          display: 'flex',
          gap: 24,
          opacity: gridOpacity,
        }}
      >
        {effects.map((effect, i) => (
          <GlassCard
            key={effect.name}
            style={{
              width: 180,
              padding: 20,
              borderColor: `${effect.color}30`,
              boxShadow: glowShadow(effect.color, 0.3),
            }}
          >
            {/* Real effect demo video */}
            <div
              style={{
                width: '100%',
                height: 120,
                borderRadius: 8,
                overflow: 'hidden',
                position: 'relative',
              }}
            >
              <Video
                src={staticFile(effect.demo)}
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover',
                }}
              />
              {/* Label overlay */}
              <div
                style={{
                  position: 'absolute',
                  bottom: 4,
                  left: 4,
                  right: 4,
                  padding: '4px 8px',
                  background: 'rgba(0,0,0,0.6)',
                  borderRadius: 4,
                  fontSize: 10,
                  color: effect.color,
                  textAlign: 'center',
                }}
              >
                LIVE DEMO
              </div>
            </div>
            <div style={{ marginTop: 16, textAlign: 'center' }}>
              <h3
                style={{
                  ...TEXT.title,
                  fontSize: 18,
                  color: effect.color,
                  margin: '0 0 4px 0',
                }}
              >
                {effect.name}
              </h3>
              <p
                style={{
                  ...TEXT.caption,
                  fontSize: 13,
                  color: COLORS.TEXT_SECONDARY,
                  margin: 0,
                }}
              >
                {effect.desc}
              </p>
            </div>
          </GlassCard>
        ))}
      </div>
      
    </AbsoluteFill>
  );
};
