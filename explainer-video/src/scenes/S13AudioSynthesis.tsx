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

const WAVEFORMS = ['sine', 'square', 'sawtooth', 'triangle'] as const;
const PRESETS = [
  { name: 'ui-blip', freq: '800Hz', type: 'sine' },
  { name: 'chime', freq: '523Hz', type: 'triangle' },
  { name: 'drone', freq: '100Hz', type: 'sawtooth' },
  { name: 'typing', freq: 'noise', type: 'filtered' },
];

export const S13AudioSynthesis: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({
    frame: Math.max(0, frame - 5),
    fps,
    config: SPRING_SMOOTH,
  });

  const contentOpacity = interpolate(frame, [25, 45], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.BG_DEEP }}>
      <GradientBackground
        glowColor={COLORS.LIME}
        glowX={0.5}
        glowY={0.5}
      />

      {/* Animated waveform background */}
      <svg
        style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: 1200,
          height: 400,
          opacity: 0.08,
        }}
      >
        {[...Array(5)].map((_, i) => (
          <path
            key={i}
            d={`M 0 200 ${[...Array(20)].map((_, j) => {
              const x = (j / 20) * 1200;
              const y = 200 + Math.sin((j + frame * 0.1 + i * 2) * 0.5) * (30 + i * 10);
              return `L ${x} ${y}`;
            }).join(' ')}`}
            stroke={COLORS.LIME}
            strokeWidth={2}
            fill="none"
          />
        ))}
      </svg>

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
          Procedural <span style={{ color: COLORS.LIME }}>Audio</span>
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
          Generate sound effects from code — no audio files needed
        </div>

        {/* Two-column content */}
        <div
          style={{
            flex: 1,
            flexDirection: 'row',
            justifyContent: 'center',
            alignItems: 'center',
            gap: 48,
            maxWidth: 900,
            width: '100%',
            opacity: contentOpacity,
          }}
        >
          {/* Left: Waveform visualization */}
          <GlassCard
            style={{
              padding: 28,
              width: 380,
              borderColor: `${COLORS.LIME}20`,
            }}
          >
            <div style={{
              ...TEXT.title,
              fontSize: 18,
              color: COLORS.LIME,
              marginBottom: 16,
            }}>
              Waveform Generation
            </div>

            <div style={{ flexDirection: 'column', gap: 14 }}>
              {WAVEFORMS.map((wave, i) => {
                const offset = frame * (0.05 + i * 0.02);
                return (
                  <div key={wave} style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
                    <span style={{
                      ...TEXT.caption,
                      fontSize: 11,
                      color: COLORS.TEXT_MUTED,
                      width: 60,
                      textTransform: 'uppercase',
                    }}>
                      {wave}
                    </span>
                    <svg width={200} height={28} style={{ opacity: 0.8 }}>
                      <path
                        d={`M 0 14 ${[...Array(50)].map((_, j) => {
                          const x = (j / 50) * 200;
                          let y = 14;
                          if (wave === 'sine') y = 14 + Math.sin((j + offset) * 0.3) * 11;
                          else if (wave === 'square') y = 14 + (Math.sin((j + offset) * 0.3) > 0 ? 11 : -11);
                          else if (wave === 'sawtooth') y = 14 + (((j + offset) % 20) / 20 - 0.5) * 22;
                          else y = 14 + ((((j + offset) % 20) / 20 < 0.5 ? ((j + offset) % 20) / 20 : 1 - ((j + offset) % 20) / 20) * 22 - 5.5);
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
          <div style={{
            flexDirection: 'column',
            gap: 10,
            width: 360,
          }}>
            <div style={{
              ...TEXT.title,
              fontSize: 18,
              color: COLORS.TEXT_PRIMARY,
              marginBottom: 4,
            }}>
              18+ Audio Presets
            </div>

            {PRESETS.map((preset, i) => {
              const presetSpring = spring({
                frame: stagger(frame, i, 5),
                fps,
                config: SPRING_SMOOTH,
              });
              return (
                <GlassCard
                  key={preset.name}
                  style={{
                    padding: '14px 18px',
                    flexDirection: 'row',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    opacity: interpolate(presetSpring, [0, 0.3], [0, 1]),
                    transform: `translateX(${interpolate(presetSpring, [0, 1], [15, 0])}px)`,
                    borderColor: `${COLORS.SEAFOAM}15`,
                  }}
                >
                  <div>
                    <span style={{
                      ...TEXT.code,
                      fontSize: 14,
                      color: COLORS.SEAFOAM,
                    }}>
                      {preset.name}
                    </span>
                    <span style={{
                      ...TEXT.caption,
                      fontSize: 11,
                      color: COLORS.TEXT_MUTED,
                      marginLeft: 10,
                    }}>
                      {preset.type}
                    </span>
                  </div>
                  <span style={{
                    ...TEXT.caption,
                    fontSize: 12,
                    color: COLORS.TEXT_SECONDARY,
                  }}>
                    {preset.freq}
                  </span>
                </GlassCard>
              );
            })}

            <div style={{
              marginTop: 4,
              padding: '10px 14px',
              background: `${COLORS.LIME}08`,
              borderRadius: 8,
              border: `1px solid ${COLORS.LIME}20`,
            }}>
              <span style={{
                ...TEXT.caption,
                fontSize: 12,
                color: COLORS.TEXT_SECONDARY,
              }}>
                + Effects: reverb, lowpass, fade, normalize, sequencing
              </span>
            </div>
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
