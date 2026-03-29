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
  glowShadow,
  FONT_DISPLAY,
} from '../lib/theme';
import { SPRING_SMOOTH, stagger, useAmbientMotion } from '../lib/animations';

const NODES = [
  { label: 'Chroma Key', icon: '🎬' },
  { label: 'Overlay', icon: '🖼️' },
  { label: 'Stabilize', icon: '📐' },
  { label: 'Watermark', icon: '💎' },
  { label: 'Subtitles', icon: '📝' },
  { label: 'Speed', icon: '⏩' },
];

export const S4ProFeatures: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const { shimmer } = useAmbientMotion(frame);

  // Node entrance
  const nodeSpring = spring({
    frame: Math.max(0, frame - 10),
    fps,
    config: SPRING_SMOOTH,
  });

  // Traveling wave pulse across nodes
  const pulseIndex = Math.floor(frame / 15) % NODES.length;

  // Demo video fade in
  const demoOpacity = interpolate(frame, [30, 60], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.BG_DEEP }}>
      <GradientBackground
        glowColor={COLORS.VIOLET_MID}
        glowX={0.5}
        glowY={0.45}
      />

      <AbsoluteFill
        style={{
          padding: 80,
          flexDirection: 'column',
        }}
      >
        {/* Title */}
        <div
          style={{
            ...TEXT.headline,
            fontSize: FONT_SIZE.HEADLINE,
            color: COLORS.TEXT_PRIMARY,
            textAlign: 'center',
            marginBottom: 60,
            opacity: interpolate(nodeSpring, [0, 0.3], [0, 1]),
          }}
        >
          <span style={{ color: COLORS.VIOLET_MID }}>Pro</span> Features
        </div>

        {/* Center: Radial node graph - centered */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            position: 'relative',
            width: '100%',
          }}
        >
          {/* Hub - enhanced glow */}
          <div
            style={{
              position: 'absolute',
              width: 110,
              height: 110,
              borderRadius: '50%',
              background: `radial-gradient(circle, ${COLORS.VIOLET_MID}50, ${COLORS.BG_CARD})`,
              border: `3px solid ${COLORS.VIOLET_MID}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: `${glowShadow(COLORS.VIOLET_MID, 0.8)}, 0 0 60px ${COLORS.VIOLET_MID}40`,
              opacity: interpolate(nodeSpring, [0, 0.5], [0, 1]),
            }}
          >
            <span style={{ 
              ...TEXT.badge, 
              color: COLORS.LIME, 
              fontSize: 18,
              textShadow: `0 0 10px ${COLORS.LIME}80`,
            }}>
              PRO
            </span>
          </div>

          {/* Nodes arranged in circle */}
          {NODES.map((node, i) => {
            const angle = (i * 360) / NODES.length - 90;
            const rad = (angle * Math.PI) / 180;
            const radius = 240;
            const x = Math.cos(rad) * radius;
            const y = Math.sin(rad) * radius;
            const isPulsing = pulseIndex === i;

            const nodeDelay = spring({
              frame: stagger(frame, i, 4),
              fps,
              config: SPRING_SMOOTH,
            });

            return (
              <React.Fragment key={node.label}>
                {/* Connecting line - thicker and brighter */}
                <div
                  style={{
                    position: 'absolute',
                    left: '50%',
                    top: '50%',
                    width: `${Math.sqrt(x * x + y * y)}px`,
                    height: 2,
                    background: `linear-gradient(90deg, ${COLORS.VIOLET_MID}60, ${COLORS.VIOLET_MID}20)`,
                    transformOrigin: '0 0',
                    transform: `rotate(${angle + 90}deg)`,
                    opacity: interpolate(nodeDelay, [0, 0.5], [0, 1]),
                  }}
                />
                {/* Node pill */}
                <div
                  style={{
                    position: 'absolute',
                    left: `calc(50% + ${x}px)`,
                    top: `calc(50% + ${y}px)`,
                    transform: `translate(-50%, -50%) scale(${interpolate(nodeDelay, [0, 1], [0.8, 1])})`,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '10px 20px',
                    borderRadius: 999,
                    background: isPulsing
                      ? `${COLORS.VIOLET_MID}30`
                      : 'rgba(27,28,30,0.8)',
                    border: `2px solid ${isPulsing ? COLORS.VIOLET_MID : 'rgba(255,255,255,0.08)'}`,
                    boxShadow: isPulsing ? `${glowShadow(COLORS.VIOLET_MID, 0.6)}, 0 0 30px ${COLORS.VIOLET_MID}30` : 'none',
                    opacity: interpolate(nodeDelay, [0, 0.3], [0, 1]),
                    transition: 'background 0.15s, border-color 0.15s',
                  }}
                >
                  <span style={{ fontSize: 20 }}>{node.icon}</span>
                  <span style={{ ...TEXT.caption, color: COLORS.TEXT_PRIMARY, fontSize: 16 }}>
                    {node.label}
                  </span>
                </div>
              </React.Fragment>
            );
          })}
        </div>

        {/* Bottom row: Real Video Demos */}
        <div
          style={{
            flexDirection: 'row',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: 24,
            height: 200,
            width: '100%',
            opacity: demoOpacity,
          }}
        >
          {/* Stabilize demo - BEFORE (Real Video) */}
          <div
            style={{
              flex: 1,
              height: 200,
              borderRadius: 12,
              overflow: 'hidden',
              border: '1px solid rgba(255,255,255,0.06)',
              position: 'relative',
            }}
          >
            <Video
              src={staticFile('demos/stabilize_before.mp4')}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
              }}
            />
            <span style={{
              position: 'absolute', top: 12, left: 12,
              ...TEXT.overline, color: COLORS.TEXT_MUTED, fontSize: 11,
              background: 'rgba(0,0,0,0.5)',
              padding: '2px 6px',
              borderRadius: 4,
            }}>BEFORE: Shaky</span>
          </div>

          {/* Arrow */}
          <div style={{ fontSize: 28, color: COLORS.VIOLET_MID }}>→</div>

          {/* Stabilize demo - AFTER (Real Video) */}
          <div
            style={{
              flex: 1,
              height: 200,
              borderRadius: 12,
              overflow: 'hidden',
              border: `1px solid ${COLORS.VIOLET_MID}30`,
              position: 'relative',
            }}
          >
            <Video
              src={staticFile('demos/stabilize_after.mp4')}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
              }}
            />
            <span style={{
              position: 'absolute', top: 12, left: 12,
              ...TEXT.overline, color: COLORS.LIME, fontSize: 11,
              background: 'rgba(0,0,0,0.5)',
              padding: '2px 6px',
              borderRadius: 4,
            }}>AFTER: Smooth</span>
          </div>

          {/* Chroma key demo - Real Video */}
          <div
            style={{
              flex: 1,
              height: 200,
              borderRadius: 12,
              overflow: 'hidden',
              border: '1px solid rgba(255,255,255,0.06)',
              position: 'relative',
            }}
          >
            {/* Show before/after with a sliding wipe */}
            <Video
              src={staticFile('demos/chroma_after.mp4')}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
              }}
            />
            <div style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: `${interpolate(frame, [90, 150], [100, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })}%`,
              height: '100%',
              overflow: 'hidden',
            }}>
              <Video
                src={staticFile('demos/chroma_before.mp4')}
                style={{
                  width: '300%',  // Compensate for container width shrink
                  height: '100%',
                  objectFit: 'cover',
                }}
              />
            </div>
            <span style={{
              position: 'absolute', bottom: 12, left: 12,
              ...TEXT.overline, color: COLORS.VIOLET_BRIGHT, fontSize: 11,
              background: 'rgba(0,0,0,0.5)',
              padding: '2px 6px',
              borderRadius: 4,
            }}>CHROMA KEY</span>
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
