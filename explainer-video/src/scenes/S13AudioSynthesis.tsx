import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, Easing } from 'remotion';
import GlassCard from '../components/GlassCard';
import { COLORS, TEXT, FONT_SIZE, glowShadow } from '../lib/theme';

// Audio Synthesis Scene for v1.0
export const S13AudioSynthesis: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  const progress = frame / (fps * 5);
  
  // Waveform animation
  const waveOffset = frame * 0.1;
  
  // Entrance animations
  const titleOpacity = interpolate(progress, [0, 0.15], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  
  const contentOpacity = interpolate(progress, [0.2, 0.35], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  
  const presets = [
    { name: 'ui-blip', freq: '800Hz', type: 'sine' },
    { name: 'chime', freq: '523Hz', type: 'triangle' },
    { name: 'drone', freq: '100Hz', type: 'sawtooth' },
    { name: 'typing', freq: 'noise', type: 'filtered' },
  ];
  
  return (
    <AbsoluteFill style={{ background: COLORS.BG_DEEP }}>
      {/* Animated waveform background */}
      <svg
        style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: 1200,
          height: 400,
          opacity: 0.1,
        }}
      >
        {[...Array(5)].map((_, i) => (
          <path
            key={i}
            d={`M 0 200 ${[...Array(20)].map((_, j) => {
              const x = (j / 20) * 1200;
              const y = 200 + Math.sin((j + waveOffset + i * 2) * 0.5) * (30 + i * 10);
              return `L ${x} ${y}`;
            }).join(' ')}`}
            stroke={COLORS.LIME}
            strokeWidth={2}
            fill="none"
          />
        ))}
      </svg>
      
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
            color: COLORS.SPRING_GREEN,
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
          Procedural Audio
        </h2>
        <p
          style={{
            ...TEXT.body,
            fontSize: FONT_SIZE.SUBTITLE,
            color: COLORS.TEXT_SECONDARY,
            marginTop: 12,
          }}
        >
          Generate sound effects from code — no external audio files needed
        </p>
      </div>
      
      {/* Main content */}
      <div
        style={{
          position: 'absolute',
          top: 280,
          left: 60,
          right: 60,
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 40,
          opacity: contentOpacity,
        }}
      >
        {/* Left: Waveform visualization */}
        <GlassCard
          style={{
            padding: 32,
            borderColor: `${COLORS.LIME}30`,
            boxShadow: glowShadow(COLORS.LIME, 0.3),
          }}
        >
          <h3
            style={{
              ...TEXT.title,
              fontSize: 20,
              color: COLORS.LIME,
              margin: '0 0 20px 0',
            }}
          >
            Waveform Generation
          </h3>
          
          {/* Animated waveforms */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {['sine', 'square', 'sawtooth', 'triangle'].map((wave, i) => {
              const offset = frame * (0.05 + i * 0.02);
              return (
                <div key={wave} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span
                    style={{
                      ...TEXT.caption,
                      fontSize: 12,
                      color: COLORS.TEXT_MUTED,
                      width: 60,
                      textTransform: 'uppercase',
                    }}
                  >
                    {wave}
                  </span>
                  <svg width={200} height={30} style={{ opacity: 0.8 }}>
                    <path
                      d={`M 0 15 ${[...Array(50)].map((_, j) => {
                        const x = (j / 50) * 200;
                        let y = 15;
                        if (wave === 'sine') {
                          y = 15 + Math.sin((j + offset) * 0.3) * 12;
                        } else if (wave === 'square') {
                          y = 15 + (Math.sin((j + offset) * 0.3) > 0 ? 12 : -12);
                        } else if (wave === 'sawtooth') {
                          y = 15 + (((j + offset) % 20) / 20 - 0.5) * 24;
                        } else if (wave === 'triangle') {
                          const phase = ((j + offset) % 20) / 20;
                          y = 15 + (phase < 0.5 ? phase * 48 - 12 : (1 - phase) * 48 - 12);
                        }
                        return `L ${x} ${y}`;
                      }).join(' ')}`}
                      stroke={COLORS.LIME}
                      strokeWidth={2}
                      fill="none"
                    />
                  </svg>
                </div>
              );
            })}
          </div>
        </GlassCard>
        
        {/* Right: Presets */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <h3
            style={{
              ...TEXT.title,
              fontSize: 20,
              color: COLORS.TEXT_PRIMARY,
              margin: '0 0 8px 0',
            }}
          >
            18+ Audio Presets
          </h3>
          
          {presets.map((preset, i) => (
            <GlassCard
              key={preset.name}
              style={{
                padding: '16px 20px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderColor: `${COLORS.SPRING_GREEN}20`,
              }}
            >
              <div>
                <span
                  style={{
                    ...TEXT.code,
                    fontSize: 14,
                    color: COLORS.SPRING_GREEN,
                  }}
                >
                  {preset.name}
                </span>
                <span
                  style={{
                    ...TEXT.caption,
                    fontSize: 12,
                    color: COLORS.TEXT_MUTED,
                    marginLeft: 12,
                  }}
                >
                  {preset.type}
                </span>
              </div>
              <span
                style={{
                  ...TEXT.caption,
                  fontSize: 12,
                  color: COLORS.TEXT_SECONDARY,
                }}
              >
                {preset.freq}
              </span>
            </GlassCard>
          ))}
          
          <div
            style={{
              marginTop: 8,
              padding: '12px 16px',
              background: `${COLORS.LIME}10`,
              borderRadius: 8,
              border: `1px solid ${COLORS.LIME}30`,
            }}
          >
            <p
              style={{
                ...TEXT.caption,
                fontSize: 13,
                color: COLORS.TEXT_SECONDARY,
                margin: 0,
              }}
            >
              + Effects: reverb, lowpass, fade, normalize, sequencing
            </p>
          </div>
        </div>
      </div>
      
    </AbsoluteFill>
  );
};
