import React from 'react';
import { COLORS, GRADIENT_PRIMARY, FONT_DISPLAY } from '../lib/theme';

interface GlowTextProps {
  glow?: boolean;
  glowColor?: string;
  style?: React.CSSProperties;
  children: React.ReactNode;
}

const GlowText: React.FC<GlowTextProps> = ({
  glow = true,
  glowColor = COLORS.NEON_CYAN,
  style,
  children,
}) => {
  const baseStyle: React.CSSProperties = {
    fontFamily: FONT_DISPLAY,
    background: GRADIENT_PRIMARY,
    backgroundClip: 'text',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    ...(glow
      ? {
          textShadow: `0 0 12px ${glowColor}60, 0 0 24px ${glowColor}20`,
        }
      : {}),
    ...style,
  };

  return <span style={baseStyle}>{children}</span>;
};

export default GlowText;
