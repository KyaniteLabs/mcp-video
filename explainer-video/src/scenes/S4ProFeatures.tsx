import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from 'remotion';
import GradientBackground from '../components/GradientBackground';
import {
  COLORS,
  FONT_SIZE,
  TEXT,
  glowShadow,
} from '../lib/theme';
import { SPRING_SMOOTH, stagger } from '../lib/animations';

const NODES = [
  { label: 'Chroma Key', color: COLORS.LIME },
  { label: 'Overlay', color: COLORS.VIOLET_MID },
  { label: 'Stabilize', color: COLORS.SEAFOAM },
  { label: 'Watermark', color: COLORS.VIOLET_BRIGHT },
  { label: 'Subtitles', color: COLORS.LIME },
  { label: 'Speed', color: COLORS.VIOLET_MID },
];

const HUB_SIZE = 120;
const NODE_RADIUS = 280;
const PILL_PADDING = '12px 28px';
const PULSE_CYCLE_FRAMES = 20;

export const S4ProFeatures: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({
    frame: Math.max(0, frame - 5),
    fps,
    config: SPRING_SMOOTH,
  });

  const pulseIndex = Math.floor(frame / PULSE_CYCLE_FRAMES) % NODES.length;

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.BG_DEEP }}>
      <GradientBackground
        glowColor={COLORS.VIOLET_MID}
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
          <span style={{ color: COLORS.VIOLET_MID }}>Pro</span> Features
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
          Advanced tools for professional results
        </div>

        {/* Radial node graph */}
        <div
          style={{
            flex: 1,
            justifyContent: 'center',
            alignItems: 'center',
            position: 'relative',
            width: '100%',
          }}
        >
          {/* Hub */}
          <div
            style={{
              position: 'absolute',
              width: HUB_SIZE,
              height: HUB_SIZE,
              borderRadius: '50%',
              background: `radial-gradient(circle, ${COLORS.VIOLET_MID}40, ${COLORS.BG_CARD})`,
              border: `2px solid ${COLORS.VIOLET_MID}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: `0 0 40px ${COLORS.VIOLET_MID}30`,
              opacity: interpolate(titleSpring, [0.2, 0.5], [0, 1]),
            }}
          >
            <span style={{
              ...TEXT.badge,
              color: COLORS.LIME,
              fontSize: 20,
            }}>
              PRO
            </span>
          </div>

          {/* Nodes */}
          {NODES.map((node, i) => {
            const angle = (i * 360) / NODES.length - 90;
            const rad = (angle * Math.PI) / 180;
            const x = Math.cos(rad) * NODE_RADIUS;
            const y = Math.sin(rad) * NODE_RADIUS;
            const isPulsing = pulseIndex === i;

            const nodeDelay = spring({
              frame: stagger(frame, i, 5),
              fps,
              config: SPRING_SMOOTH,
            });

            const pulseScale = isPulsing
              ? interpolate(
                  Math.sin((frame % PULSE_CYCLE_FRAMES) / PULSE_CYCLE_FRAMES * Math.PI),
                  [0, 1],
                  [1, 1.08],
                )
              : 1;

            return (
              <React.Fragment key={node.label}>
                {/* Connecting line */}
                <div
                  style={{
                    position: 'absolute',
                    left: '50%',
                    top: '50%',
                    width: `${NODE_RADIUS}px`,
                    height: 1,
                    background: `linear-gradient(90deg, ${COLORS.VIOLET_MID}40, ${COLORS.VIOLET_MID}10)`,
                    transformOrigin: '0 0',
                    transform: `rotate(${angle + 90}deg)`,
                    opacity: interpolate(nodeDelay, [0.1, 0.4], [0, 1]),
                  }}
                />
                {/* Node pill */}
                <div
                  style={{
                    position: 'absolute',
                    left: `calc(50% + ${x}px)`,
                    top: `calc(50% + ${y}px)`,
                    transform: `translate(-50%, -50%) scale(${interpolate(nodeDelay, [0, 1], [0.6, 1]) * pulseScale})`,
                    padding: PILL_PADDING,
                    borderRadius: 999,
                    background: isPulsing
                      ? `${node.color}20`
                      : `${COLORS.BG_CARD}`,
                    border: `1.5px solid ${isPulsing ? `${node.color}80` : 'rgba(255,255,255,0.08)'}`,
                    boxShadow: isPulsing ? `0 0 20px ${node.color}30` : 'none',
                    opacity: interpolate(nodeDelay, [0.1, 0.4], [0, 1]),
                  }}
                >
                  <span style={{
                    ...TEXT.caption,
                    color: isPulsing ? node.color : COLORS.TEXT_PRIMARY,
                    fontSize: 16,
                    fontWeight: 500,
                  }}>
                    {node.label}
                  </span>
                </div>
              </React.Fragment>
            );
          })}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
