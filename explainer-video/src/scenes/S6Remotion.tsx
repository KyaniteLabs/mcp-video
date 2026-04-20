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
  FONT_DISPLAY,
  FONT_MONO,
  TEXT,
  glowShadow,
} from '../lib/theme';
import { SPRING_SMOOTH, stagger } from '../lib/animations';

const TOOLS = [
  'remotion_render', 'remotion_still', 'remotion_validate',
  'remotion_studio', 'remotion_compositions', 'remotion_scaffold',
  'remotion_to_mcpvideo',
];

const PIPELINE_STAGES = [
  { label: 'Spec', color: COLORS.LIME },
  { label: 'Components', color: COLORS.VIOLET_MID },
  { label: 'Render', color: COLORS.VIOLET_BRIGHT },
  { label: 'Export', color: COLORS.LIME },
];

const TREE_LINES = [
  'src/',
  '├── Root.tsx',
  '├── scenes/',
  '│   ├── S1Hook.tsx',
  '│   ├── S2Solution.tsx',
  '│   └── S3CoreEditing.tsx',
  '└── lib/',
  '    └── theme.ts',
];

export const S6Remotion: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Browser entrance
  const browserSpring = spring({
    frame: Math.max(0, frame - 5),
    fps,
    config: SPRING_SMOOTH,
  });

  // Pipeline dots travel
  const pipelineProgress = (frame % 90) / 90;

  // Ticker scroll
  const tickerOffset = interpolate(frame, [0, 180], [0, -600]);

  // Tree line reveal
  const treeLineCount = Math.min(
    TREE_LINES.length,
    Math.floor(interpolate(frame, [20, 80], [0, TREE_LINES.length], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    })),
  );

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.BG_DEEP }}>
      <GradientBackground
        glowColor={COLORS.VIOLET_MID}
        glowX={0.5}
        glowY={0.4}
      />

      {/* Subtle grid pattern */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
          pointerEvents: 'none',
        }}
      />

      <AbsoluteFill
        style={{
          padding: 60,
          flexDirection: 'column',
          gap: 24,
        }}
      >
        {/* Title */}
        <div
          style={{
            ...TEXT.headline,
            fontSize: FONT_SIZE.HEADLINE,
            color: COLORS.TEXT_PRIMARY,
            textAlign: 'center',
          }}
        >
          <span style={{ color: COLORS.VIOLET_MID }}>Remotion</span> Integration
        </div>
        <div
          style={{
            ...TEXT.subtitle,
            fontSize: 20,
            color: COLORS.TEXT_SECONDARY,
            textAlign: 'center',
            opacity: interpolate(browserSpring, [0, 0.3], [0, 1]),
            marginTop: 4,
          }}
        >
          The React framework for programmatic video
        </div>

        {/* Browser mockup */}
        <div
          style={{
            opacity: interpolate(browserSpring, [0, 0.3], [0, 1]),
            transform: `translateY(${interpolate(browserSpring, [0, 1], [30, 0])}px)`,
            width: 800,
            alignSelf: 'center',
          }}
        >
          {/* Browser chrome */}
          <div
            style={{
              background: COLORS.BG_CARD,
              borderRadius: '12px 12px 0 0',
              padding: '12px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              borderBottom: '1px solid rgba(255,255,255,0.06)',
            }}
          >
            <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#ff5f56' }} />
            <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#ffbd2e' }} />
            <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#27c93f' }} />
            <div
              style={{
                flex: 1,
                textAlign: 'center',
                fontFamily: FONT_MONO,
                fontSize: 13,
                color: COLORS.TEXT_MUTED,
                background: 'rgba(0,0,0,0.3)',
                borderRadius: 6,
                padding: '4px 12px',
              }}
            >
              localhost:3000
            </div>
          </div>
          {/* Browser body */}
          <div
            style={{
              background: COLORS.BG_DEEP,
              borderRadius: '0 0 12px 12px',
              padding: 20,
              border: '1px solid rgba(255,255,255,0.06)',
              borderTop: 'none',
              flexDirection: 'row',
              gap: 32,
              height: 300,
            }}
          >
            {/* File tree */}
            <div style={{ flex: 1 }}>
              {TREE_LINES.slice(0, treeLineCount).map((line, i) => (
                <div
                  key={i}
                  style={{
                    fontFamily: FONT_MONO,
                    fontSize: 15,
                    color: line.includes('│') || line.includes('├') || line.includes('└')
                      ? COLORS.TEXT_MUTED
                      : COLORS.NEON_CYAN,
                    height: 24,
                    opacity: interpolate(
                      Math.max(0, frame - 20 - i * 5),
                      [0, 10],
                      [0, 1],
                      { extrapolateRight: 'clamp' },
                    ),
                  }}
                >
                  {line}
                </div>
              ))}
            </div>
            {/* Video preview mockup */}
            <div
              style={{
                flex: 1,
                borderRadius: 8,
                overflow: 'hidden',
                border: '1px solid rgba(255,255,255,0.06)',
                position: 'relative',
              }}
            >
              <div
                style={{
                  width: '100%',
                  height: '100%',
                  background: `linear-gradient(${135 + Math.sin(frame * 0.02) * 15}deg, #1a1a2e 0%, #0f3460 40%, #533483 70%, #e94560 100%)`,
                }}
              >
                {/* Play button overlay */}
                <div
                  style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    width: 48,
                    height: 48,
                    borderRadius: '50%',
                    background: 'rgba(0,0,0,0.5)',
                    border: `2px solid ${COLORS.NEON_CYAN}60`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <div
                    style={{
                      width: 0,
                      height: 0,
                      borderTop: '10px solid transparent',
                      borderBottom: '10px solid transparent',
                      borderLeft: '16px solid #fff',
                      marginLeft: 4,
                    }}
                  />
                </div>
                {/* Progress bar */}
                <div
                  style={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    right: 0,
                    height: 4,
                    background: 'rgba(255,255,255,0.1)',
                  }}
                >
                  <div
                    style={{
                      width: `${(frame % 120) / 120 * 100}%`,
                      height: '100%',
                      background: COLORS.LIME,
                      boxShadow: glowShadow(COLORS.LIME, 0.3),
                    }}
                  />
                </div>
                {/* Time code */}
                <div
                  style={{
                    position: 'absolute',
                    bottom: 12,
                    right: 12,
                    fontFamily: FONT_MONO,
                    fontSize: 11,
                    color: 'rgba(255,255,255,0.6)',
                  }}
                >
                  00:{String(Math.floor((frame % 120) / 2)).padStart(2, '0')} / 01:00
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Pipeline flow */}
        <div
          style={{
            flexDirection: 'row',
            gap: 0,
            alignSelf: 'center',
            alignItems: 'center',
          }}
        >
          {PIPELINE_STAGES.map((stage, i) => (
            <React.Fragment key={stage.label}>
              <div
                style={{
                  padding: '8px 20px',
                  borderRadius: 8,
                  background: `${stage.color}15`,
                  border: `1px solid ${stage.color}40`,
                  ...TEXT.caption,
                  color: stage.color,
                  fontSize: 14,
                }}
              >
                {stage.label}
              </div>
              {i < PIPELINE_STAGES.length - 1 && (
                <div
                  style={{
                    width: 60,
                    height: 2,
                    background: `linear-gradient(90deg, ${stage.color}40, ${PIPELINE_STAGES[i + 1].color}40)`,
                    position: 'relative',
                  }}
                >
                  {/* Traveling dot */}
                  <div
                    style={{
                      position: 'absolute',
                      top: -3,
                      left: `${pipelineProgress * 100}%`,
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      background: COLORS.LIME,
                      boxShadow: glowShadow(COLORS.LIME, 0.5),
                    }}
                  />
                </div>
              )}
            </React.Fragment>
          ))}
        </div>

        {/* Bottom ticker */}
        <div
          style={{
            flexDirection: 'row',
            gap: 8,
            alignSelf: 'center',
            overflow: 'hidden',
            height: 36,
            alignItems: 'center',
            transform: `translateX(${tickerOffset}px)`,
          }}
        >
          {TOOLS.map((tool, i) => (
            <div
              key={tool}
              style={{
                padding: '4px 12px',
                borderRadius: 999,
                background: `${COLORS.VIOLET_MID}15`,
                border: `1px solid ${COLORS.VIOLET_MID}30`,
                fontFamily: FONT_MONO,
                fontSize: 13,
                color: COLORS.TEXT_SECONDARY,
                whiteSpace: 'nowrap',
              }}
            >
              {tool}
            </div>
          ))}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
