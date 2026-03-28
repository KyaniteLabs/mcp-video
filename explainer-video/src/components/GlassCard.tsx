import React from 'react';
import { useCurrentFrame } from 'remotion';
import { GLASS_STYLE, glowShadow, SPACING } from '../lib/theme';

interface GlassCardProps {
  accentColor?: string;
  accentTop?: boolean;
  children: React.ReactNode;
  style?: React.CSSProperties;
  shimmer?: boolean;
}

const GlassCard: React.FC<GlassCardProps> = ({
  accentColor,
  accentTop = false,
  children,
  style,
  shimmer = false,
}) => {
  const frame = useCurrentFrame();

  // Shimmer sweep every ~90 frames (3s at 30fps)
  const shimmerProgress = shimmer
    ? ((frame % 90) / 90)
    : 0;

  return (
    <div
      style={{
        ...GLASS_STYLE,
        borderRadius: 12,
        padding: `${SPACING.LG}px`,
        position: 'relative',
        overflow: 'hidden',
        ...(accentTop && accentColor
          ? { borderTop: `2px solid ${accentColor}` }
          : {}),
        ...style,
      }}
    >
      {/* Shimmer sweep overlay */}
      {shimmer && (
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: `${shimmerProgress * 200 - 50}%`,
            width: '50%',
            height: '100%',
            background: `linear-gradient(90deg, transparent, rgba(255,255,255,0.03), transparent)`,
            pointerEvents: 'none',
          }}
        />
      )}
      {children}
    </div>
  );
};

export default GlassCard;
