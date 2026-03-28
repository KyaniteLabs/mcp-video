import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { COLORS, cardBorder, FONT_DISPLAY, FONT_BODY } from '../lib/theme';
import { entrance } from '../lib/animations';

interface FloatingCardProps {
  title: string;
  body: string;
  accent?: string;
  delay?: number;
}

const FloatingCard: React.FC<FloatingCardProps> = ({
  title,
  body,
  accent = COLORS.NEON_CYAN,
  delay = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const { opacity, translateY, scale } = entrance(frame, fps, delay);

  const containerStyle: React.CSSProperties = {
    background: `linear-gradient(180deg, ${COLORS.BG_CARD}, ${COLORS.BG_DEEP})`,
    borderTop: '1px solid rgba(255, 255, 255, 0.06)',
    borderRadius: 16,
    borderLeft: `4px solid ${accent}`,
    border: cardBorder,
    borderLeftWidth: 4,
    borderLeftStyle: 'solid',
    borderLeftColor: accent,
    padding: 32,
    opacity,
    transform: `translateY(${translateY}px) scale(${scale})`,
  };

  return (
    <div style={containerStyle}>
      <div
        style={{
          color: COLORS.TEXT_PRIMARY,
          fontSize: 24,
          fontFamily: FONT_DISPLAY,
          fontWeight: 600,
          marginBottom: 12,
        }}
      >
        {title}
      </div>
      <div
        style={{
          color: COLORS.TEXT_SECONDARY,
          fontSize: 18,
          fontFamily: FONT_BODY,
          lineHeight: 1.4,
        }}
      >
        {body}
      </div>
    </div>
  );
};

export default FloatingCard;
