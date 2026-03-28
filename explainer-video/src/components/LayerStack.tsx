import React from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';
import { COLORS, cardBorder, FONT_DISPLAY, FONT_MONO } from '../lib/theme';
import { SPRING_BOUNCE } from '../lib/animations';

interface Layer {
  label: string;
  detail?: string;
}

interface LayerStackProps {
  layers: Layer[];
}

export const LayerStack: React.FC<LayerStackProps> = ({ layers }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 0,
      }}
    >
      {layers.map((layer, i) => {
        const localFrame = Math.max(0, frame - i * 12);
        const sp = spring({
          frame: localFrame,
          fps,
          config: SPRING_BOUNCE,
        });
        const opacity = interpolate(sp, [0, 1], [0, 1]);
        const translateY = interpolate(sp, [0, 1], [60, 0]);

        return (
          <React.Fragment key={i}>
            <div
              style={{
                background: `linear-gradient(180deg, ${COLORS.BG_CARD}, ${COLORS.BG_DEEP})`,
                borderTop: '1px solid rgba(255, 255, 255, 0.06)',
                borderRadius: 10,
                padding: '16px 24px',
                border: cardBorder,
                opacity,
                transform: `translateY(${translateY}px)`,
                minWidth: 280,
              }}
            >
              <div
                style={{
                  color: COLORS.TEXT_PRIMARY,
                  fontSize: 18,
                  fontFamily: FONT_DISPLAY,
                  fontWeight: 600,
                  lineHeight: 1.4,
                }}
              >
                {layer.label}
              </div>
              {layer.detail && (
                <div
                  style={{
                    color: COLORS.TEXT_MUTED,
                    fontSize: 14,
                    fontFamily: FONT_MONO,
                    marginTop: 4,
                    lineHeight: 1.4,
                  }}
                >
                  {layer.detail}
                </div>
              )}
            </div>
            {i < layers.length - 1 && (
              <div
                style={{
                  color: COLORS.NEON_PURPLE,
                  fontSize: 20,
                  lineHeight: 1,
                  opacity,
                  padding: '4px 0',
                }}
              >
                &darr;
              </div>
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};
