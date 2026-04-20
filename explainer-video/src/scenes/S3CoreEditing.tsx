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
import { SPRING_GLASS, stagger } from '../lib/animations';

// ── Feature definitions ────────────────────────────────────────────
const FEATURES = [
  { icon: '✂️', label: 'Trim & Cut', desc: 'Precision frame control' },
  { icon: '🔗', label: 'Merge', desc: 'Multi-clip composition' },
  { icon: '🎨', label: 'Color Grade', desc: 'Cinematic presets' },
  { icon: '🔊', label: 'Audio Sync', desc: 'Smart normalization' },
  { icon: '📐', label: 'Resize', desc: 'Any aspect ratio' },
  { icon: '⚡', label: 'Convert', desc: 'Format flexibility' },
];

// ── Constants ──────────────────────────────────────────────────────
const CYCLE_PERIOD = 35; // frames per highlighted card
const STAGGER_DELAY = 6; // frames between card entrances
const GRID_GAP = 24;
const GRID_MAX_WIDTH = 900;
const LAYOUT_PADDING = 80;
const CARD_PADDING = 24;
const ICON_SIZE = 28;
const CARD_LABEL_SIZE = 20;
const CARD_DESC_SIZE = 14;

export const S3CoreEditing: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Determine which card is currently highlighted (cycles through all 6)
  const activeIndex = Math.floor(frame / CYCLE_PERIOD) % FEATURES.length;

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.BG_DEEP }}>
      <GradientBackground glowColor={COLORS.NEON_PURPLE} />

      <AbsoluteFill
        style={{
          flexDirection: 'column',
          padding: LAYOUT_PADDING,
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        {/* Title */}
        <div
          style={{
            ...TEXT.headline,
            fontSize: FONT_SIZE.HEADLINE,
            color: COLORS.TEXT_PRIMARY,
            marginBottom: 12,
            opacity: interpolate(
              spring({ frame, fps, config: SPRING_GLASS }),
              [0, 1],
              [0, 1],
            ),
            transform: `translateY(${interpolate(
              spring({ frame, fps, config: SPRING_GLASS }),
              [0, 1],
              [20, 0],
            )}px)`,
          }}
        >
          Core Editing
        </div>

        {/* Subtitle */}
        <div
          style={{
            ...TEXT.subtitle,
            fontSize: FONT_SIZE.SUBTITLE,
            color: COLORS.TEXT_MUTED,
            marginBottom: 48,
            opacity: interpolate(
              spring({ frame: stagger(frame, 0, 4), fps, config: SPRING_GLASS }),
              [0, 1],
              [0, 1],
            ),
            transform: `translateY(${interpolate(
              spring({ frame: stagger(frame, 0, 4), fps, config: SPRING_GLASS }),
              [0, 1],
              [12, 0],
            )}px)`,
          }}
        >
          Everything you need, one tool call away
        </div>

        {/* 3x2 Feature Grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: GRID_GAP,
            maxWidth: GRID_MAX_WIDTH,
            width: '100%',
            alignSelf: 'center',
          }}
        >
          {FEATURES.map((feature, i) => {
            const cardSpring = spring({
              frame: stagger(frame, i, STAGGER_DELAY),
              fps,
              config: SPRING_GLASS,
            });

            const isActive = i === activeIndex;
            const accentColor = isActive ? COLORS.LIME : COLORS.VIOLET_MID;

            // Entrance animation: opacity + scale + slight rotation
            const entranceOpacity = interpolate(cardSpring, [0, 0.3], [0, 1]);
            const entranceScale = interpolate(cardSpring, [0, 1], [0.92, 1]);
            const entranceRotate = interpolate(cardSpring, [0, 1], [2, 0]);

            // Active card glow intensity (subtle pulse)
            const glowIntensity = isActive
              ? interpolate(
                  Math.sin(frame * 0.08),
                  [-1, 1],
                  [0.3, 0.6],
                )
              : 0;

            return (
              <div
                key={feature.label}
                style={{
                  opacity: entranceOpacity,
                  transform: `scale(${entranceScale}) rotate(${entranceRotate}deg)`,
                  boxShadow: glowIntensity > 0
                    ? glowShadow(COLORS.LIME, glowIntensity)
                    : undefined,
                  borderRadius: 12,
                }}
              >
                <GlassCard
                  accentColor={accentColor}
                  accentTop
                  shimmer
                  style={{ padding: CARD_PADDING }}
                >
                  <div style={{ textAlign: 'center' }}>
                    <div
                      style={{
                        fontSize: ICON_SIZE,
                        marginBottom: 8,
                      }}
                    >
                      {feature.icon}
                    </div>
                    <div
                      style={{
                        ...TEXT.title,
                        fontSize: CARD_LABEL_SIZE,
                        color: COLORS.TEXT_PRIMARY,
                        marginBottom: 4,
                      }}
                    >
                      {feature.label}
                    </div>
                    <div
                      style={{
                        ...TEXT.caption,
                        fontSize: CARD_DESC_SIZE,
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
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
