import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { COLORS, FONT_DISPLAY } from '../lib/theme';

interface VersionBadgeProps {
  version: string;
}

export const VersionBadge: React.FC<VersionBadgeProps> = ({ version }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        top: 24,
        right: 24,
        border: `1px solid ${COLORS.NEON_CYAN}`,
        background: 'rgba(0, 240, 255, 0.15)',
        borderRadius: 999,
        padding: '4px 14px',
        fontSize: 14,
        fontFamily: FONT_DISPLAY,
        color: COLORS.NEON_CYAN,
        opacity,
      }}
    >
      {version}
    </div>
  );
};
