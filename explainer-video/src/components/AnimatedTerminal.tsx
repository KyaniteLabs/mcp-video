import React from 'react';
import { useCurrentFrame } from 'remotion';
import { COLORS, FONT_MONO } from '../lib/theme';

interface AnimatedTerminalProps {
  lines: string[];
  framesPerLine?: number;
  showCursor?: boolean;
}

export const AnimatedTerminal: React.FC<AnimatedTerminalProps> = ({
  lines,
  framesPerLine = 12,
  showCursor = true,
}) => {
  const frame = useCurrentFrame();

  const cursor = frame % 30 < 15 ? '█' : ' ';

  // Character-by-character typing: completed lines + partial current line
  const completedLines = Math.min(lines.length, Math.floor(frame / framesPerLine));
  const currentLineFrame = frame % framesPerLine;
  const isTypingLine = completedLines < lines.length;
  const currentLineChars = isTypingLine
    ? Math.floor((currentLineFrame / framesPerLine) * lines[completedLines].length)
    : 0;

  return (
    <div
      style={{
        background: `linear-gradient(180deg, ${COLORS.BG_ELEVATED}, ${COLORS.BG_CARD})`,
        borderTop: '1px solid rgba(255, 255, 255, 0.06)',
        borderRadius: 12,
        overflow: 'hidden',
        border: `1px solid ${COLORS.NEON_PURPLE}20`,
      }}
    >
      {/* Title bar */}
      <div
        style={{
          height: 36,
          backgroundColor: COLORS.BG_DEEP,
          display: 'flex',
          alignItems: 'center',
          padding: '0 14px',
          gap: 8,
        }}
      >
        <div
          style={{
            width: 10,
            height: 10,
            borderRadius: '50%',
            backgroundColor: '#FF5F56',
          }}
        />
        <div
          style={{
            width: 10,
            height: 10,
            borderRadius: '50%',
            backgroundColor: '#FFBD2E',
          }}
        />
        <div
          style={{
            width: 10,
            height: 10,
            borderRadius: '50%',
            backgroundColor: '#27C93F',
          }}
        />
        <span
          style={{
            color: COLORS.TEXT_MUTED,
            fontSize: 13,
            marginLeft: 8,
          }}
        >
          Terminal
        </span>
      </div>

      {/* Body */}
      <div
        style={{
          padding: '16px 20px',
          fontFamily: FONT_MONO,
          fontSize: 20,
        }}
      >
        {/* Completed lines (full) */}
        {lines.slice(0, completedLines).map((line, i) => (
          <div key={i} style={{ color: COLORS.NEON_GREEN }}>
            {line}
          </div>
        ))}
        {/* Partial active line with cursor */}
        {isTypingLine && (
          <div style={{ color: COLORS.NEON_GREEN }}>
            {lines[completedLines].slice(0, currentLineChars)}
            {showCursor ? cursor : ''}
          </div>
        )}
        {/* Cursor-only after all lines done */}
        {!isTypingLine && showCursor && (
          <div style={{ color: COLORS.NEON_GREEN }}>{cursor}</div>
        )}
      </div>
    </div>
  );
};
