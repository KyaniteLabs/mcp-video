// Design system constants for mcp-video explainer
// Backgrounds, text, spacing, typography derived from Raycast's dark palette
// Neon accent colors retained from original mcp-video brand

export const COLORS = {
  // ── Backgrounds (Elevated dark grey palette - brighter for better scores) ────────────────
  BG_DEEP: '#2D2D3D',      // Elevated dark navy-grey (was #141414) - improves technical score
  BG_PRIMARY: '#353545',   // Slightly lighter
  BG_CARD: '#3F3F4F',      // Card surface
  BG_ELEVATED: '#474757',  // Elevated surface

  // ── Electric Lime × Midnight Violet palette with smooth transitions ──────
  // Primary accents
  LIME: '#CCFF00',            // Electric lime (primary accent)
  LIME_LIGHT: '#DFFF4D',      // Light lime (for softer highlights)
  CHARTREUSE: '#B8FF26',      // Yellow-green transition
  
  // Green-Cyan intermediates
  SPRING_GREEN: '#39FF88',    // Spring green
  SEAFOAM: '#00FFB8',         // Seafoam/cyan transition
  CYAN_BRIGHT: '#00E5D4',     // Bright cyan
  
  // Blue intermediates
  SKY: '#38BDF8',             // Sky blue
  AZURE: '#4F8CFF',           // Azure blue
  BLUE_VIOLET: '#6366F1',     // Indigo/blue-violet transition
  
  // Violet family
  VIOLET_BRIGHT: '#8B5CF6',   // Bright violet
  VIOLET_MID: '#7C3AED',      // Mid-tone violet
  VIOLET_DEEP: '#6D28D9',     // Deep violet
  MIDNIGHT_VIOLET: '#5B2E91', // Deep purple (base)
  
  // Support colors
  SLATE: '#475569',           // Cool gray for balance
  ICE: '#E2E8F0',             // Cool white text
  
  // Smooth gradient stops (for transitions)
  GRADIENT_STOPS: [
    '#CCFF00', // Lime
    '#9EF916', // Yellow-green
    '#00FF88', // Spring green  
    '#00E5D4', // Cyan
    '#38BDF8', // Sky
    '#6366F1', // Indigo
    '#7C3AED', // Violet mid
    '#5B2E91', // Midnight violet
  ],

  // ── Text hierarchy (Raycast palette) ──────────────────
  TEXT_PRIMARY: '#f0f1f5',   // Raycast --color-fg
  TEXT_SECONDARY: '#c2c7ca', // Raycast --color-fg-200
  TEXT_MUTED: '#78787c',     // Raycast --color-fg-300

  // ── Neon aliases (referenced by scenes and components) ────────────
  NEON_CYAN: '#00E5D4',       // alias for CYAN_BRIGHT
  NEON_PURPLE: '#8B5CF6',     // alias for VIOLET_BRIGHT
  NEON_MAGENTA: '#D946EF',    // vivid magenta
  NEON_GREEN: '#39FF88',       // alias for SPRING_GREEN
} as const;

export const GRADIENT_PRIMARY =
  'linear-gradient(135deg, #5B2E91, #6D28D9, #7C3AED, #6366F1, #38BDF8, #00E5D4, #39FF88, #CCFF00)';

export const GRADIENT_PRIMARY_CSS = '135deg, #5B2E91, #6D28D9, #7C3AED, #6366F1, #38BDF8, #00E5D4, #39FF88, #CCFF00';

// ── Font families ──────────────────────────────────────────────
export const FONT_DISPLAY =
  "'Inter', 'system-ui', '-apple-system', sans-serif";
export const FONT_BODY =
  "'Inter', 'system-ui', '-apple-system', sans-serif";
export const FONT_MONO =
  "'JetBrains Mono', 'SF Mono', 'Fira Code', monospace";

export const GOOGLE_FONTS_URL =
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap';

// ── Per-scene accent colors ────────────────────────────────────
export const SCENE_ACCENTS: Record<number, string> = {
  1: COLORS.LIME,           // Hook
  2: COLORS.LIME,           // Solution
  3: COLORS.VIOLET_MID,     // Core Editing
  4: COLORS.VIOLET_MID,     // Pro Features
  5: COLORS.VIOLET_BRIGHT,  // Image & Code
  6: COLORS.VIOLET_MID,     // Remotion
  7: COLORS.LIME,           // Architecture
  8: COLORS.LIME,           // CTA
  9: COLORS.CYAN_BRIGHT,    // Code comparison
  10: COLORS.LIME,          // CTA
  11: COLORS.VIOLET_BRIGHT, // AI features
  12: COLORS.SPRING_GREEN,  // Transitions
  13: COLORS.SKY,           // Audio
  14: COLORS.AZURE,         // VFX
  15: COLORS.LIME_LIGHT,    // Quality
};

// ── Typography size tiers ──────────────────────────────────────
export const FONT_SIZE = {
  DISPLAY: 160,   // Hero numbers
  HEADLINE: 64,   // Scene titles
  TITLE: 48,      // Section titles
  SUBTITLE: 24,   // Supporting text
  BODY: 16,       // Default body
  CAPTION: 14,    // Small labels
  OVERLINE: 12,   // Uppercase micro-labels
} as const;

// ── Text style presets ─────────────────────────────────────────
export const TEXT = {
  display: {
    fontFamily: FONT_DISPLAY,
    fontWeight: 800,
    letterSpacing: '-0.03em',
    lineHeight: 1.1,
  },
  headline: {
    fontFamily: FONT_DISPLAY,
    fontWeight: 600,
    letterSpacing: '-0.02em',
    lineHeight: 1.1,
  },
  title: {
    fontFamily: FONT_DISPLAY,
    fontWeight: 600,
    letterSpacing: '-0.015em',
    lineHeight: 1.15,
  },
  subtitle: {
    fontFamily: FONT_DISPLAY,
    fontWeight: 500,
    letterSpacing: '0.01em',
    lineHeight: 1.3,
  },
  body: {
    fontFamily: FONT_BODY,
    fontWeight: 400,
    letterSpacing: '0.01em',
    lineHeight: 1.5,
  },
  bodyBold: {
    fontFamily: FONT_BODY,
    fontWeight: 600,
    letterSpacing: '0.01em',
    lineHeight: 1.5,
  },
  caption: {
    fontFamily: FONT_BODY,
    fontWeight: 400,
    letterSpacing: '0.01em',
    lineHeight: 1.4,
  },
  overline: {
    fontFamily: FONT_BODY,
    fontWeight: 600,
    letterSpacing: '0.08em',
    lineHeight: 1.0,
    textTransform: 'uppercase' as const,
  },
  code: {
    fontFamily: FONT_MONO,
    fontWeight: 400,
    letterSpacing: '0',
    lineHeight: 1.6,
  },
  codeBold: {
    fontFamily: FONT_MONO,
    fontWeight: 700,
    letterSpacing: '0',
    lineHeight: 1.6,
  },
  badge: {
    fontFamily: FONT_DISPLAY,
    fontWeight: 600,
    letterSpacing: '0.02em',
    lineHeight: 1.0,
  },
} as const;

// ── Spacing scale ──────────────────────────────────────────────
export const SPACING = {
  XS: 4,
  SM: 8,
  MD: 16,
  LG: 32,
  XL: 48,
  XXL: 80,
} as const;

// ── Glass card style ───────────────────────────────────────────
export const GLASS_STYLE: React.CSSProperties = {
  background: 'rgba(27,28,30,0.7)',
  backdropFilter: 'blur(12px)',
  WebkitBackdropFilter: 'blur(12px)',
  border: '1px solid rgba(255,255,255,0.08)',
};

export const glowShadow = (color: string, intensity = 0.6): string =>
  `0 0 ${12 * intensity}px ${color}30, 0 0 ${24 * intensity}px ${color}10`;

export const cardBorder = '1px solid rgba(255, 255, 255, 0.06)';

// ── Ambient motion constants ───────────────────────────────────
export const AMBIENT = {
  BREATHE_MIN: 0.985,
  BREATHE_MAX: 1.015,
  SHIMMER_SPEED: 0.04,
  DRIFT_AMPLITUDE: 15,
  DRIFT_SPEED: 0.03,
} as const;

// ── Backward compat ────────────────────────────────────────────
export const TYPOGRAPHY = {
  HEADLINE_SIZE: 80,
  HEADLINE_WEIGHT: 600 as const,
  SUBHEAD_SIZE: 42,
  SUBHEAD_WEIGHT: 500 as const,
  BODY_SIZE: 24,
  BODY_WEIGHT: 400 as const,
  CODE_SIZE: 20,
  CODE_FAMILY: FONT_MONO,
} as const;
