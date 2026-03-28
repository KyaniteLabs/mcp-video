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
  GRADIENT_PRIMARY,
  FONT_MONO,
  TEXT,
  glowShadow,
} from '../lib/theme';
import { SPRING_SMOOTH, SPRING_DECAY } from '../lib/animations';

const MOVIEPY_LINES = [
  'from moviepy.editor import VideoFileClip',
  'from moviepy.video.fx.all import colorize',
  '',
  'clip = VideoFileClip("input.mp4")',
  'clip = clip.subclip(0, 10)',
  'clip = clip.resize((1920, 1080))',
  'clip = colorize(clip, saturation=1.5)',
  'clip = clip.set_fps(30)',
  'clip = clip.set_duration(10)',
  'clip.write_videofile("out.mp4")',
];

const MCPVIDEO_LINE = 'video.trim("input.mp4", start=0, end=10)';

export const S9CodeComparison: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const leftSpring = spring({ frame, fps, config: SPRING_DECAY });

  const rightSpring = spring({
    frame: Math.max(0, frame - 25),
    fps,
    config: { damping: 15, stiffness: 120, mass: 0.8 },
  });

  const linesVisible = Math.min(
    MOVIEPY_LINES.length,
    Math.floor(interpolate(frame, [10, 80], [0, MOVIEPY_LINES.length], {
      extrapolateRight: 'clamp',
    })),
  );

  const charsVisible = Math.min(
    MCPVIDEO_LINE.length,
    Math.floor(interpolate(frame, [40, 70], [0, MCPVIDEO_LINE.length], {
      extrapolateRight: 'clamp',
    })),
  );

  const bottomOpacity = interpolate(frame, [80, 100], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.BG_DEEP }}>
      <GradientBackground
        glowColor={COLORS.NEON_CYAN}
        glowX={0.5}
        glowY={0.4}
      />

      <AbsoluteFill
        style={{
          flexDirection: 'row',
          padding: 80,
          gap: 60,
        }}
      >
        {/* Left: MoviePy (red tint) */}
        <div
          style={{
            flex: 1,
            opacity: interpolate(leftSpring, [0, 0.3], [0, 1]),
            transform: `translateX(${interpolate(leftSpring, [0, 1], [20, 0])}px)`,
          }}
        >
          <div
            style={{
              ...TEXT.overline,
              color: '#FF6B6B',
              fontSize: 14,
              marginBottom: 12,
            }}
          >
            MoviePy
          </div>
          <div
            style={{
              background: 'rgba(255,60,60,0.05)',
              border: '1px solid rgba(255,60,60,0.1)',
              borderRadius: 12,
              padding: 20,
              fontFamily: FONT_MONO,
              fontSize: 13,
              lineHeight: 1.8,
            }}
          >
            {MOVIEPY_LINES.map((line, i) => (
              <div
                key={i}
                style={{
                  color: i < linesVisible ? COLORS.TEXT_SECONDARY : 'rgba(255,255,255,0.1)',
                  whiteSpace: 'pre',
                }}
              >
                {line}
              </div>
            ))}
          </div>
        </div>

        {/* Center divider */}
        <div
          style={{
            width: 3,
            alignSelf: 'stretch',
            background: `linear-gradient(180deg, transparent, ${COLORS.TEXT_MUTED}20, transparent)`,
          }}
        />

        {/* Right: mcp-video (green tint) */}
        <div
          style={{
            flex: 1,
            opacity: interpolate(rightSpring, [0, 0.3], [0, 1]),
            transform: `translateX(${interpolate(rightSpring, [0, 1], [-20, 0])}px)`,
          }}
        >
          <div
            style={{
              ...TEXT.overline,
              color: COLORS.NEON_GREEN,
              fontSize: 14,
              marginBottom: 12,
            }}
          >
            mcp-video
          </div>
          <div
            style={{
              background: 'rgba(0,255,136,0.05)',
              border: `1px solid ${COLORS.NEON_GREEN}30`,
              borderRadius: 12,
              padding: 20,
              fontFamily: FONT_MONO,
              fontSize: 16,
              lineHeight: 1.8,
              boxShadow: glowShadow(COLORS.NEON_GREEN, 0.2),
            }}
          >
            <div style={{ color: COLORS.NEON_GREEN }}>
              {'>'}
            </div>
            <div style={{ color: COLORS.TEXT_PRIMARY }}>
              {MCPVIDEO_LINE.slice(0, charsVisible)}
            </div>
            <div style={{ color: COLORS.NEON_GREEN }}>
              {charsVisible >= MCPVIDEO_LINE.length ? "')" : ''}
            </div>
            <span
              style={{
                color: COLORS.NEON_CYAN,
                opacity: charsVisible >= MCPVIDEO_LINE.length
                  ? Math.floor(frame / 15) % 2 === 0 ? 1 : 0
                  : 0,
              }}
            >
              ▊
            </span>
          </div>
        </div>
      </AbsoluteFill>

      {/* Bottom text */}
      <div
        style={{
          position: 'absolute',
          bottom: 80,
          left: '50%',
          transform: 'translateX(-50%)',
          opacity: bottomOpacity,
          textAlign: 'center',
        }}
      >
        <span
          style={{
            ...TEXT.subtitle,
            fontSize: 28,
            background: GRADIENT_PRIMARY,
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          10 lines → 1 tool call
        </span>
      </div>
    </AbsoluteFill>
  );
};
