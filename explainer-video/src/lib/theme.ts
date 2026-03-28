// Design system constants for mcp-video explainer
// Backgrounds, text, spacing, typography derived from Raycast's dark palette
// Neon accent colors retained from original mcp-video brand

export const COLORS = {
  // ── Backgrounds (Raycast dark palette) ────────────────
  BG_DEEP: '#07080a',      // Raycast --grey-900 (body bg)
  BG_PRIMARY: '#111214',   // Raycast --grey-700 (elevated surface)
  BG_CARD: '#1b1c1e',      // Raycast --grey-600 (cards, panels)
  BG_ELEVATED: '#2f3031',  // Raycast --grey-500 (popovers, modals)

  // ── Neon accents (retained from mcp-video brand) ──────
  NEON_CYAN: '#00F0FF',
  NEON_MAGENTA: '#FF00FF',
  NEON_PURPLE: '#8B5CF6',
  NEON_GREEN: '#00FF88',
  NEON_ORANGE: '#FF6B35',

  // ── Text hierarchy (Raycast palette) ──────────────────
  TEXT_PRIMARY: '#f0f1f5',   // Raycast --color-fg
  TEXT_SECONDARY: '#c2c7ca', // Raycast --color-fg-200
  TEXT_MUTED: '#78787c',     // Raycast --color-fg-300
} as const;

export const GRADIENT_PRIMARY =
  'linear-gradient(135deg, #00F0FF, #8B5CF6, #FF00FF)';

export const GRADIENT_PRIMARY_CSS = '135deg, #00F0FF, #8B5CF6, #FF00FF';

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
  1: COLORS.NEON_CYAN,      // Hook
  2: COLORS.NEON_CYAN,      // Solution
  3: COLORS.NEON_PURPLE,    // Core Editing
  4: COLORS.NEON_PURPLE,    // Pro Features
  5: COLORS.NEON_MAGENTA,   // Image & Code (magenta→cyan handled in scene)
  6: COLORS.NEON_PURPLE,    // Remotion
  7: COLORS.NEON_CYAN,      // Architecture
  8: COLORS.NEON_CYAN,      // CTA
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
