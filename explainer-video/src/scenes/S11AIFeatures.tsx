import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, Easing, Video, staticFile } from 'remotion';
import GlassCard from '../components/GlassCard';
import { COLORS, TEXT, FONT_SIZE, glowShadow } from '../lib/theme';

// REAL demo video from mcp-video operation on pottery footage
const upscaleDemo = staticFile('demos/upscale_demo.mp4');

// AI Features Scene for v1.0 - Now showing real capabilities
export const S11AIFeatures: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  const progress = frame / (fps * 6);
  
  // Entrance animations
  const titleY = interpolate(progress, [0, 0.15], [40, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  
  const titleOpacity = interpolate(progress, [0, 0.15], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  
  // Staggered card entrances
  const cardDelay = 0.1;
  const getCardProgress = (index: number) => 
    interpolate(progress, [cardDelay * index, cardDelay * index + 0.2], [0, 1], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
      easing: Easing.out(Easing.cubic),
    });
  
  const aiFeatures = [
    { icon: '🎤', title: 'Silence Removal', desc: 'Auto-remove dead air', color: COLORS.LIME },
    { icon: '📝', title: 'Transcription', desc: 'Whisper-powered STT', color: COLORS.CHARTREUSE },
    { icon: '🎬', title: 'Scene Detection', desc: 'ML-enhanced cuts', color: COLORS.SPRING_GREEN },
    { icon: '🎵', title: 'Stem Separation', desc: 'Isolate vocals, drums', color: COLORS.SEAFOAM },
    { icon: '🔍', title: 'AI Upscale', desc: 'Super-resolution 2x/4x', color: COLORS.CYAN_BRIGHT },
    { icon: '🎨', title: 'Color Grading', desc: 'Auto color correction', color: COLORS.SKY },
    { icon: '🔊', title: 'Spatial Audio', desc: '3D audio positioning', color: COLORS.AZURE },
  ];
  
  return (
    <AbsoluteFill style={{ background: COLORS.BG_DEEP }}>
      {/* Subtle gradient orb */}
      <div
        style={{
          position: 'absolute',
          width: 600,
          height: 600,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${COLORS.VIOLET_MID}20 0%, transparent 70%)`,
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
        }}
      />
      
      {/* Header */}
      <div
        style={{
          position: 'absolute',
          top: 80,
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
          AI-Powered Editing
        </h2>
        <p
          style={{
            ...TEXT.body,
            fontSize: FONT_SIZE.SUBTITLE,
            color: COLORS.TEXT_SECONDARY,
            marginTop: 12,
            maxWidth: 600,
            marginLeft: 'auto',
            marginRight: 'auto',
          }}
        >
          Machine learning features for intelligent video processing
        </p>
      </div>
      
      {/* AI Features Grid */}
      <div
        style={{
          position: 'absolute',
          top: 240,
          left: 60,
          right: 60,
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: 20,
        }}
      >
        {aiFeatures.slice(0, 4).map((feature, i) => {
          const p = getCardProgress(i);
          return (
            <GlassCard
              key={feature.title}
              style={{
                padding: '24px 20px',
                textAlign: 'center',
                opacity: p,
                transform: `translateY(${(1 - p) * 30}px)`,
                borderColor: `${feature.color}30`,
                boxShadow: glowShadow(feature.color, 0.4),
              }}
            >
              <div style={{ fontSize: 40, marginBottom: 12 }}>{feature.icon}</div>
              <h3
                style={{
                  ...TEXT.title,
                  fontSize: 18,
                  color: COLORS.TEXT_PRIMARY,
                  margin: '0 0 8px 0',
                }}
              >
                {feature.title}
              </h3>
              <p
                style={{
                  ...TEXT.caption,
                  fontSize: 14,
                  color: COLORS.TEXT_SECONDARY,
                  margin: 0,
                }}
              >
                {feature.desc}
              </p>
            </GlassCard>
          );
        })}
      </div>
      
      {/* Second row */}
      <div
        style={{
          position: 'absolute',
          top: 420,
          left: '50%',
          transform: 'translateX(-50%)',
          display: 'flex',
          gap: 20,
        }}
      >
        {aiFeatures.slice(4).map((feature, i) => {
          const p = getCardProgress(i + 4);
          return (
            <GlassCard
              key={feature.title}
              style={{
                width: 200,
                padding: '24px 20px',
                textAlign: 'center',
                opacity: p,
                transform: `translateY(${(1 - p) * 30}px)`,
                borderColor: `${feature.color}30`,
                boxShadow: glowShadow(feature.color, 0.4),
              }}
            >
              <div style={{ fontSize: 40, marginBottom: 12 }}>{feature.icon}</div>
              <h3
                style={{
                  ...TEXT.title,
                  fontSize: 18,
                  color: COLORS.TEXT_PRIMARY,
                  margin: '0 0 8px 0',
                }}
              >
                {feature.title}
              </h3>
              <p
                style={{
                  ...TEXT.caption,
                  fontSize: 14,
                  color: COLORS.TEXT_SECONDARY,
                  margin: 0,
                }}
              >
                {feature.desc}
              </p>
            </GlassCard>
          );
        })}
      </div>
      
      {/* REAL Demo Video - AI Upscale on Pottery Footage */}
      <div
        style={{
          position: 'absolute',
          bottom: 100,
          left: '50%',
          transform: 'translateX(-50%)',
          opacity: getCardProgress(7),
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <div
          style={{
            ...TEXT.caption,
            fontSize: 12,
            color: COLORS.TEXT_MUTED,
            marginBottom: 8,
          }}
        >
          AI Upscale Demo — Real pottery footage 360p → 720p
        </div>
        <GlassCard
          style={{
            padding: 8,
            borderColor: `${COLORS.CYAN_BRIGHT}40`,
            boxShadow: `0 0 30px ${COLORS.CYAN_BRIGHT}20`,
          }}
        >
          <Video
            src={upscaleDemo}
            style={{
              width: 480,
              height: 270,
              borderRadius: 8,
            }}
          />
        </GlassCard>
        <div
          style={{
            display: 'flex',
            gap: 20,
            marginTop: 12,
          }}
        >
          <span style={{ ...TEXT.caption, fontSize: 12, color: COLORS.TEXT_SECONDARY }}>
            ← Low-res input
          </span>
          <span style={{ ...TEXT.caption, fontSize: 12, color: COLORS.CYAN_BRIGHT }}>
            AI Upscale 2x →
          </span>
        </div>
      </div>
      
    </AbsoluteFill>
  );
};
