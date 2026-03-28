import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { COLORS, cardBorder, FONT_DISPLAY, FONT_BODY } from '../lib/theme';
import { entrance } from '../lib/animations';

interface ToolCardProps {
  name: string;
  icon: string;
  description: string;
  delay?: number;
}

const ToolCard: React.FC<ToolCardProps> = ({
  name,
  icon,
  description,
  delay = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const { opacity, translateY, scale } = entrance(frame, fps, delay);

  const containerStyle: React.CSSProperties = {
    background: `linear-gradient(180deg, ${COLORS.BG_CARD}, ${COLORS.BG_DEEP})`,
    borderTop: '1px solid rgba(255, 255, 255, 0.06)',
    borderRadius: 12,
    border: cardBorder,
    padding: 24,
    opacity,
    transform: `translateY(${translateY}px) scale(${scale})`,
  };

  return (
    <div style={containerStyle}>
      <div style={{ fontSize: 40, marginBottom: 12 }}>{icon}</div>
      <div
        style={{
          color: COLORS.TEXT_PRIMARY,
          fontSize: 20,
          fontFamily: FONT_DISPLAY,
          fontWeight: 700,
          marginBottom: 8,
        }}
      >
        {name}
      </div>
      <div style={{ color: COLORS.TEXT_SECONDARY, fontSize: 16, fontFamily: FONT_BODY, lineHeight: 1.4 }}>
        {description}
      </div>
    </div>
  );
};

export default ToolCard;
