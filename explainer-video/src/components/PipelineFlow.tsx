import React from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';
import { COLORS, cardBorder, FONT_DISPLAY } from '../lib/theme';
import { SPRING_BOUNCE } from '../lib/animations';

interface PipelineFlowProps {
  steps: string[];
}

export const PipelineFlow: React.FC<PipelineFlowProps> = ({ steps }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        gap: 0,
      }}
    >
      {steps.map((step, i) => {
        const localFrame = Math.max(0, frame - i * 10);
        const sp = spring({
          frame: localFrame,
          fps,
          config: SPRING_BOUNCE,
        });
        const opacity = interpolate(sp, [0, 1], [0, 1]);
        const translateX = interpolate(sp, [0, 1], [30, 0]);

        return (
          <React.Fragment key={i}>
            <div
              style={{
                background: `linear-gradient(180deg, ${COLORS.BG_CARD}, ${COLORS.BG_DEEP})`,
                borderTop: '1px solid rgba(255, 255, 255, 0.06)',
                borderRadius: 8,
                padding: '12px 20px',
                color: COLORS.TEXT_PRIMARY,
                fontFamily: FONT_DISPLAY,
                border: cardBorder,
                lineHeight: 1.4,
                opacity,
                transform: `translateX(${translateX}px)`,
                whiteSpace: 'nowrap',
              }}
            >
              {step}
            </div>
            {i < steps.length - 1 && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  position: 'relative',
                  width: 60,
                  height: 2,
                  margin: '0 8px',
                  opacity,
                }}
              >
                <div
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    height: 2,
                    backgroundColor: `${COLORS.NEON_PURPLE}80`,
                  }}
                />
                <div
                  style={{
                    position: 'absolute',
                    top: -3,
                    left: `${interpolate(frame % 60, [0, 60], [0, 100])}%`,
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    backgroundColor: COLORS.NEON_CYAN,
                    boxShadow: `0 0 8px ${COLORS.NEON_CYAN}`,
                  }}
                />
                <span
                  style={{
                    position: 'absolute',
                    right: -6,
                    color: COLORS.NEON_PURPLE,
                    fontSize: 18,
                    fontWeight: 700,
                    lineHeight: 1,
                  }}
                >
                  &gt;
                </span>
              </div>
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};
