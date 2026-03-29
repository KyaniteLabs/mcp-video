import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, Easing } from 'remotion';
import GlassCard from '../components/GlassCard';
import { BurnedCaption } from '../components/BurnedCaption';
import { COLORS, TEXT, FONT_SIZE, glowShadow } from '../lib/theme';

// Visual Effects Scene for v1.0
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
  
  // Demo image with different effects
  const DemoImage: React.FC<{ effect: string; color: string }> = ({ effect, color }) => (
    <div
      style={{
        width: '100%',
        height: 120,
        background: `linear-gradient(135deg, ${color}30, ${COLORS.BG_CARD})`,
        borderRadius: 8,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Effect preview visualization */}
      {effect === 'vignette' && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: 'radial-gradient(circle, transparent 40%, rgba(0,0,0,0.6) 100%)',
          }}
        />
      )}
      {effect === 'chroma' && (
        <>
          <div style={{ position: 'absolute', color: '#ff0000', fontSize: 40, transform: 'translate(-3px, -3px)', opacity: 0.7 }}>Fx</div>
          <div style={{ position: 'absolute', color: '#00ff00', fontSize: 40, opacity: 0.7 }}>Fx</div>
          <div style={{ position: 'absolute', color: '#0000ff', fontSize: 40, transform: 'translate(3px, 3px)', opacity: 0.7 }}>Fx</div>
        </>
      )}
      {effect === 'scanlines' && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.3) 2px, rgba(0,0,0,0.3) 4px)',
          }}
        />
      )}
      {effect === 'noise' && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            opacity: 0.3,
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
          }}
        />
      )}
      {effect === 'glow' && (
        <div
          style={{
            fontSize: 48,
            color: color,
            textShadow: `0 0 20px ${color}, 0 0 40px ${color}`,
            filter: 'blur(0.5px)',
          }}
        >
          ✦
        </div>
      )}
      
      <span style={{ position: 'relative', zIndex: 1, fontSize: 24, color: COLORS.TEXT_SECONDARY }}>
        {effect === 'chroma' ? '' : effect === 'glow' ? '' : 'Fx'}
      </span>
    </div>
  );
  
  const effects = [
    { name: 'Vignette', desc: 'Darkened edges', icon: '◐', color: COLORS.VIOLET_MID },
    { name: 'Chromatic', desc: 'RGB separation', icon: '⚡', color: COLORS.LIME },
    { name: 'Scanlines', desc: 'CRT overlay', icon: '☰', color: COLORS.CYAN_BRIGHT },
    { name: 'Noise', desc: 'Film grain', icon: '✻', color: COLORS.TEXT_MUTED },
    { name: 'Glow', desc: 'Bloom effect', icon: '✦', color: COLORS.VIOLET_BRIGHT },
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
      
      {/* Effects Grid */}
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
            <DemoImage 
              effect={effect.name.toLowerCase().replace('chromatic', 'chroma')} 
              color={effect.color} 
            />
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
      
      <BurnedCaption text="Vignette, chromatic aberration, scanlines, noise, and glow" />
    </AbsoluteFill>
  );
};
