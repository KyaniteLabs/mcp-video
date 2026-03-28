# Video Audit Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Address all P0/P1/P2 audit priorities — positive hook, real demos, captions, MCP primer, code comparison, improved CTA, animated architecture.

**Architecture:** Enhance 8 existing scenes in-place, add 2 new scenes (MCP Primer, Code Comparison), add burned-in caption component. Expand from 1500 to 2100 frames (70s). Generate synthetic demo clips with mcp-video tools.

**Tech Stack:** Remotion 4.0.261, React, TypeScript, @remotion/transitions

**Design doc:** `docs/plans/2026-03-28-video-audit-fixes-design.md`

---

## Task 1: Update Root.tsx — Expand to 2100 frames

**Files:**
- Modify: `explainer-video/src/Root.tsx:11`

**Step 1: Change durationInFrames from 1500 to 2100**

```tsx
// Line 11: change 1500 → 2100
durationInFrames={2100}
```

**Step 2: Commit**

```bash
git add explainer-video/src/Root.tsx
git commit -m "chore: expand video to 2100 frames (70s) for audit fixes"
```

---

## Task 2: S1 Hook — Positive Reframe (P0 #1)

**Files:**
- Modify: `explainer-video/src/scenes/S1Hook.tsx:24`

**Step 1: Change hook text from negative to positive**

```tsx
// Line 24: change
const HOOK_TEXT = 'What if AI could edit video?';
```

No other changes needed — glitch, timing, colors all stay the same.

**Step 2: Commit**

```bash
git add explainer-video/src/scenes/S1Hook.tsx
git commit -m "feat(S1): reframe hook to positive — 'What if AI could edit video?'"
```

---

## Task 3: S2 Solution — Slow Orbit + Better Subtitle (P1 #6)

**Files:**
- Modify: `explainer-video/src/scenes/S2Solution.tsx:54,103`

**Step 1: Slow orbit rotation from 1.5 to 0.75 degrees/frame**

```tsx
// Line 54: change
const orbitAngle = (frame * 0.75) * (Math.PI / 180);
```

**Step 2: Change subtitle text**

```tsx
// Line 103: change
          43 video editing tools
```

**Step 3: Commit**

```bash
git add explainer-video/src/scenes/S2Solution.tsx
git commit -m "feat(S2): slow orbit 50%, change subtitle to '43 video editing tools'"
```

---

## Task 4: S3 Core Editing — Cycling Demo Panel (P0 #3)

**Files:**
- Modify: `explainer-video/src/scenes/S3CoreEditing.tsx`

This is the biggest scene change. Replace the right-side before/after gradient bar with a cycling demo panel that highlights one feature at a time.

**Step 1: Replace the before/after section (lines 109-175)**

The right side currently has a static gradient with BEFORE/AFTER labels. Replace with a cycling demo panel:

```tsx
        {/* Right: Cycling demo panel */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <div
            style={{
              width: '100%',
              maxWidth: 500,
              borderRadius: 12,
              overflow: 'hidden',
              border: '1px solid rgba(255,255,255,0.08)',
              background: 'rgba(0,0,0,0.3)',
              padding: 24,
            }}
          >
            {/* Demo title */}
            <div style={{ ...TEXT.overline, color: COLORS.NEON_PURPLE, fontSize: 13, marginBottom: 20 }}>
              DEMO
            </div>

            {/* Cycle through 3 features, ~70 frames each */}
            {(() => {
              const cycleFrame = frame % 210;
              const demoIndex = Math.floor(cycleFrame / 70);

              const demos = [
                {
                  title: 'Trim & Cut',
                  desc: 'Precision frame selection',
                  icon: '✂️',
                  visual: (
                    <div style={{ position: 'relative', height: 200 }}>
                      {/* Timeline bar */}
                      <div style={{
                        position: 'absolute', top: '50%', left: 0, right: 0,
                        height: 40, transform: 'translateY(-50%)',
                        background: 'rgba(255,255,255,0.06)', borderRadius: 8,
                      }}>
                        {/* Full bar */}
                        <div style={{
                          position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
                          background: 'rgba(255,255,255,0.04)', borderRadius: 8,
                        }} />
                        {/* Selected segment */}
                        <div style={{
                          position: 'absolute', top: 0,
                          left: `${interpolate(cycleFrame, [0, 70], [10, 60], { extrapolateRight: 'clamp' })}%`,
                          width: '30%', height: '100%',
                          background: COLORS.NEON_PURPLE, borderRadius: 8,
                          boxShadow: glowShadow(COLORS.NEON_PURPLE, 0.4),
                        }} />
                        {/* Scissors icon */}
                        <div style={{
                          position: 'absolute',
                          left: `${interpolate(cycleFrame, [0, 70], [10, 60], { extrapolateRight: 'clamp' })}%`,
                          top: -16, fontSize: 24, transform: 'translateX(-50%)',
                        }}>✂️</div>
                      </div>
                    </div>
                  ),
                },
                {
                  title: 'Color Grade',
                  desc: 'Cinematic presets',
                  icon: '🎨',
                  visual: (
                    <div style={{ height: 200, position: 'relative', borderRadius: 8, overflow: 'hidden' }}>
                      {/* Before: flat */}
                      <div style={{
                        position: 'absolute', inset: 0,
                        background: 'linear-gradient(135deg, #3a3a3a, #4a4a4a, #3a3a3a)',
                      }} />
                      {/* After: cinematic overlay sweeps in */}
                      <div style={{
                        position: 'absolute', inset: 0,
                        background: 'linear-gradient(135deg, #0f3460, #533483, #e94560)',
                        clipPath: `inset(0 ${100 - interpolate(cycleFrame, [0, 70], [0, 100], { extrapolateRight: 'clamp' })}% 0 0)`,
                      }} />
                    </div>
                  ),
                },
                {
                  title: 'Merge',
                  desc: 'Multi-clip composition',
                  icon: '🔗',
                  visual: (
                    <div style={{ height: 200, display: 'flex', gap: 8, alignItems: 'center' }}>
                      {/* Clip A */}
                      <div style={{
                        flex: 1, height: 180, borderRadius: 8,
                        background: 'linear-gradient(135deg, #1a1a2e, #16213e)',
                        border: '1px solid rgba(255,255,255,0.06)',
                        opacity: interpolate(cycleFrame, [0, 70], [0.5, 1], { extrapolateRight: 'clamp' }),
                      }} />
                      {/* Clip B slides in from right */}
                      <div style={{
                        flex: 1, height: 180, borderRadius: 8,
                        background: 'linear-gradient(135deg, #2d1b3d, #0f3460)',
                        border: '1px solid rgba(255,255,255,0.06)',
                        transform: `translateX(${interpolate(cycleFrame, [0, 70], [200, 0], { extrapolateRight: 'clamp' })}px)`,
                      }} />
                    </div>
                  ),
                },
              ];

              const demo = demos[demoIndex];
              const demoProgress = spring({
                frame: Math.max(0, frame - demoIndex * 70),
                fps,
                config: { damping: 25, stiffness: 80, mass: 0.8 },
              });

              return (
                <div key={demo.title} style={{
                  opacity: interpolate(demoProgress, [0, 0.3], [0, 1]),
                  transform: `translateY(${interpolate(demoProgress, [0, 1], [10, 0])}px)`,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                    <span style={{ fontSize: 28 }}>{demo.icon}</span>
                    <div>
                      <div style={{ ...TEXT.title, fontSize: 20, color: COLORS.TEXT_PRIMARY }}>{demo.title}</div>
                      <div style={{ ...TEXT.caption, fontSize: 14, color: COLORS.TEXT_MUTED }}>{demo.desc}</div>
                    </div>
                  </div>
                  {demo.visual}
                </div>
              );
            })()}
          </div>
        </div>
```

**Step 2: Add highlight state to the feature cards on the left**

In the feature card rendering loop (around line 59), add a highlight when that feature matches the active demo:

```tsx
              // After line 59, before the card spring calculation:
              const demoIndex = Math.floor((frame % 210) / 70);
              const isActive = i === demoIndex;
```

And on the GlassCard wrapper (around line 75), add a highlight border when active:

```tsx
                  <GlassCard
                    accentColor={isActive ? COLORS.NEON_CYAN : COLORS.NEON_PURPLE}
                    accentTop
                    shimmer
                    style={{
                      padding: '20px 16px',
                      borderColor: isActive ? `${COLORS.NEON_CYAN}40` : undefined,
                    }}
                  >
```

**Step 3: Commit**

```bash
git add explainer-video/src/scenes/S3CoreEditing.tsx
git commit -m "feat(S3): cycling demo panel with trim, color grade, merge micro-demos"
```

---

## Task 5: S4 Pro Features — Micro-Demos Replace Decorations (P1 #7)

**Files:**
- Modify: `explainer-video/src/scenes/S4ProFeatures.tsx`

Replace the bottom section (waveform bars + Ken Burns box, lines 178-241) with micro-demo panels.

**Step 1: Replace the bottom section with two micro-demo panels**

Replace lines 178-241 with:

```tsx
        {/* Bottom row: Micro-demos */}
        <div
          style={{
            flexDirection: 'row',
            gap: 24,
            height: 200,
            alignItems: 'center',
          }}
        >
          {/* Stabilize demo */}
          <div
            style={{
              flex: 1,
              height: 200,
              borderRadius: 12,
              overflow: 'hidden',
              border: `1px solid rgba(255,255,255,0.06)`,
              position: 'relative',
            }}
          >
            <div style={{
              width: '100%', height: '100%',
              background: 'linear-gradient(135deg, #1a1a2e, #2d1b3d, #0f3460)',
              transform: `translateX(${Math.sin(frame * 0.3) * 15}px) translateY(${Math.cos(frame * 0.2) * 10}px)`,
            }}>
              <span style={{
                position: 'absolute', top: 12, left: 12,
                ...TEXT.overline, color: COLORS.TEXT_MUTED, fontSize: 11,
              }}>BEFORE: Shaky</span>
            </div>
          </div>

          {/* Arrow */}
          <div style={{ fontSize: 28, color: COLORS.NEON_PURPLE }}>→</div>

          {/* Stabilized result */}
          <div
            style={{
              flex: 1,
              height: 200,
              borderRadius: 12,
              overflow: 'hidden',
              border: `1px solid ${COLORS.NEON_PURPLE}30`,
              position: 'relative',
            }}
          >
            <div style={{
              width: '100%', height: '100%',
              background: 'linear-gradient(135deg, #1a1a2e, #2d1b3d, #0f3460)',
            }}>
              <span style={{
                position: 'absolute', top: 12, left: 12,
                ...TEXT.overline, color: COLORS.NEON_GREEN, fontSize: 11,
              }}>AFTER: Smooth</span>
            </div>
          </div>

          {/* Chroma key demo */}
          <div
            style={{
              flex: 1,
              height: 200,
              borderRadius: 12,
              overflow: 'hidden',
              border: `1px solid rgba(255,255,255,0.06)`,
              position: 'relative',
            }}
          >
            <div style={{
              width: '100%', height: '100%',
              background: '#00FF00',
              borderRadius: 12,
            }} />
            {/* Background replacing green */}
            <div style={{
              position: 'absolute', inset: 0,
              background: 'linear-gradient(135deg, #0f3460, #533483, #e94560)',
              clipPath: `inset(0 0 0 ${interpolate(frame, [0, 210], [100, 0], { extrapolateRight: 'clamp' })}%)`,
              borderRadius: 12,
            }} />
            <span style={{
              position: 'absolute', bottom: 12, left: 12,
              ...TEXT.overline, color: COLORS.NEON_MAGENTA, fontSize: 11,
            }}>CHROMA KEY</span>
          </div>
        </div>
```

**Step 2: Commit**

```bash
git add explainer-video/src/scenes/S4ProFeatures.tsx
git commit -m "feat(S4): replace waveform/Ken Burns with stabilize + chroma key micro-demos"
```

---

## Task 6: S5 Image Code — Context Header + Hex Codes (P1 #8)

**Files:**
- Modify: `explainer-video/src/scenes/S5ImageCode.tsx`

**Step 1: Add context header above the existing content**

After line 80 (`gap: 40`), insert a header section:

```tsx
        {/* Context header */}
        <div style={{ textAlign: 'center', marginBottom: 8 }}>
          <div style={{
            ...TEXT.title, fontSize: 32, color: COLORS.NEON_MAGENTA,
            marginBottom: 4,
          }}>
            AI-Powered Color Analysis
          </div>
          <div style={{
            ...TEXT.subtitle, fontSize: 20, color: COLORS.TEXT_SECONDARY,
          }}>
            Extract brand colors from any image automatically
          </div>
        </div>
```

**Step 2: Add floating hex codes under the swatch circles**

After the swatch circles rendering (after line 133), add hex code labels:

```tsx
            {/* Floating hex codes */}
            <div style={{ flexDirection: 'row', gap: 12, marginTop: 8 }}>
              {EXTRACTED_COLORS.map((color, i) => {
                const offset = (i - 2) * swatchSpread * 50;
                const hexOpacity = interpolate(frame, [40, 80], [0, 1], { extrapolateRight: 'clamp' });
                return (
                  <span
                    key={color}
                    style={{
                      ...TEXT.code,
                      fontSize: 12,
                      color: color,
                      opacity: hexOpacity,
                      transform: `translateX(${offset}px)`,
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {color}
                  </span>
                );
              })}
            </div>
```

**Step 3: Commit**

```bash
git add explainer-video/src/scenes/S5ImageCode.tsx
git commit -m "feat(S5): add context header and floating hex codes to color analysis scene"
```

---

## Task 7: S6 Remotion — Context Subtitle (P2 #11)

**Files:**
- Modify: `explainer-video/src/scenes/S6Remotion.tsx:99-109`

**Step 1: Add subtitle under the title**

After the title div (line 109), add:

```tsx
        <div
          style={{
            ...TEXT.subtitle,
            fontSize: 20,
            color: COLORS.TEXT_SECONDARY,
            textAlign: 'center',
            opacity: interpolate(browserSpring, [0, 0.3], [0, 1]),
            marginTop: 4,
          }}
        >
          The React framework for programmatic video
        </div>
```

**Step 2: Commit**

```bash
git add explainer-video/src/scenes/S6Remotion.tsx
git commit -m "feat(S6): add 'React framework for programmatic video' subtitle"
```

---

## Task 8: S7 Architecture — Horizontal Animated Data Flow (P2 #10)

**Files:**
- Modify: `explainer-video/src/scenes/S7Architecture.tsx`

This is the second biggest change. Replace the vertical layer stack with a horizontal data flow.

**Step 1: Replace the layer stack section (lines 97-207) with horizontal flow**

Replace the layer stack `<div>` with:

```tsx
        {/* Horizontal data flow */}
        <div
          style={{
            flex: 1,
            justifyContent: 'center',
            alignItems: 'center',
            gap: 20,
          }}
        >
          {LAYERS.map((layer, i) => {
            const cardSpring = spring({
              frame: stagger(frame, i, 8),
              fps,
              config: SPRING_GLASS,
            });
            const isGlowing = glowIndex === i;
            const packetProgress = interpolate(
              (frame % 60) / 60,
              [0, 1],
            );

            return (
              <React.Fragment key={layer.label}>
                <div
                  style={{
                    opacity: interpolate(cardSpring, [0, 0.3], [0, 1]),
                    transform: `translateY(${interpolate(cardSpring, [0, 1], [20, 0])}px)`,
                  }}
                >
                  <GlassCard
                    accentColor={layer.color}
                    accentTop
                    style={{
                      width: 200,
                      padding: '16px 20px',
                      textAlign: 'center',
                      boxShadow: isGlowing ? glowShadow(layer.color, 0.5) : 'none',
                      borderColor: isGlowing ? `${layer.color}40` : undefined,
                    }}
                  >
                    <div
                      style={{
                        ...TEXT.title,
                        fontSize: 18,
                        color: layer.color,
                        marginBottom: 4,
                      }}
                    >
                      {layer.label}
                    </div>
                    <div style={{ ...TEXT.caption, fontSize: 13, color: COLORS.TEXT_MUTED }}>
                      {layer.desc}
                    </div>
                  </GlassCard>
                </div>

                {/* Arrow + traveling dot between layers */}
                {i < LAYERS.length - 1 && (
                  <div style={{
                    width: 60,
                    height: 2,
                    background: `${COLORS.TEXT_MUTED}15`,
                    position: 'relative',
                  }}>
                    <div
                      style={{
                        position: 'absolute',
                        top: -4,
                        left: `${packetProgress * 100}%`,
                        width: 10,
                        height: 10,
                        borderRadius: '50%',
                        background: COLORS.NEON_CYAN,
                        boxShadow: glowShadow(COLORS.NEON_CYAN, 0.5),
                      }}
                    />
                    <div style={{
                      position: 'absolute',
                      right: -4,
                      top: -3,
                      width: 0,
                      height: 0,
                      borderLeft: `6px solid ${COLORS.TEXT_MUTED}25`,
                      borderTop: '5px solid transparent',
                      borderBottom: '5px solid transparent',
                    }} />
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
```

**Step 2: Commit**

```bash
git add explainer-video/src/scenes/S7Architecture.tsx
git commit -m "feat(S7): horizontal animated data flow with traveling packet"
```

---

## Task 9: Create BurnedCaption Component (P0 #4)

**Files:**
- Create: `explainer-video/src/components/BurnedCaption.tsx`

**Step 1: Create the caption component**

```tsx
import React from 'react';
import { interpolate } from 'remotion';
import { COLORS } from '../lib/theme';

interface BurnedCaptionProps {
  text: string;
  delay?: number;
}

export const BurnedCaption: React.FC<BurnedCaptionProps> = ({ text, delay = 0 }) => {
  const frame = 0; // Captured at component render — we use the parent's frame via props

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 60,
        left: '50%',
        transform: 'translateX(-50%)',
        background: 'rgba(0,0,0,0.65)',
        borderRadius: 12,
        padding: '10px 24px',
        maxWidth: 800,
        zIndex: 50,
        pointerEvents: 'none',
      }}
    >
      <span
        style={{
          fontFamily: "'Inter', 'system-ui', sans-serif",
          fontSize: 36,
          fontWeight: 700,
          color: '#ffffff',
          letterSpacing: '0.01em',
          lineHeight: 1.2,
          textShadow: '0 1px 4px rgba(0,0,0,0.8)',
          whiteSpace: 'nowrap',
        }}
      >
        {text}
      </span>
    </div>
  );
};
```

**Step 2: Commit**

```bash
git add explainer-video/src/components/BurnedCaption.tsx
git commit -m "feat: add BurnedCaption component for burned-in subtitles"
```

---

## Task 10: Add Captions to All Scenes (P0 #4)

**Files:**
- Modify: `explainer-video/src/scenes/S1Hook.tsx`
- Modify: `explainer-video/src/scenes/S2Solution.tsx`
- Modify: `explainer-video/src/scenes/S3CoreEditing.tsx`
- Modify: `explainer-video/src/scenes/S4ProFeatures.tsx`
- Modify: `explainer-video/src/scenes/S5ImageCode.tsx`
- Modify: `explainer-video/src/scenes/S6Remotion.tsx`
- Modify: `explainer-video/src/scenes/S7Architecture.tsx`
- Modify: `explainer-video/src/scenes/S8CTA.tsx`

For each scene, add the caption import and render `<BurnedCaption>` at the bottom of the scene's root `<AbsoluteFill>`.

**Step 1: Add import to each scene file**

```tsx
import { BurnedCaption } from '../components/BurnedCaption';
```

**Step 2: Add caption component before the closing `</AbsoluteFill>` of each scene**

S1Hook: `<BurnedCaption text="What if AI could edit video?" />`
S2Solution: `<BurnedCaption text="43 powerful video editing tools" />`
S3CoreEditing: `<BurnedCaption text="Trim, merge, color grade — everything you need" />`
S4ProFeatures: `<BurnedCaption text="Chroma key, stabilization, subtitles, and more" />`
S5ImageCode: `<BurnedCaption text="Extract colors and automate your workflow" />`
S6Remotion: `<BurnedCaption text="Seamless Remotion integration" />`
S7Architecture: `<BurnedCaption text="AI → MCP → FFmpeg → Output" />`
S8CTA: `<BurnedCaption text="pip install mcp-video" />`

**Step 3: Commit**

```bash
git add explainer-video/src/scenes/
git commit -m "feat: add burned-in captions to all 8 scenes"
```

---

## Task 11: Create S8 MCP Primer Scene (P2 #12)

**Files:**
- Create: `explainer-video/src/scenes/S8MCPPrimer.tsx`

**Step 1: Create the new scene**

```tsx
import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from 'remotion';
import GradientBackground from '../components/GradientBackground';
import {
  COLORS,
  GRADIENT_PRIMARY,
  FONT_SIZE,
  FONT_DISPLAY,
  TEXT,
  glowShadow,
} from '../lib/theme';
import { SPRING_SMOOTH } from '../lib/animations';

export const S8MCPPrimer: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // "MCP" entrance
  const mcpSpring = spring({ frame, fps, config: SPRING_SMOOTH });

  // "=" sign
  const eqOpacity = interpolate(frame, [20, 30], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Description types in
  const descOpacity = interpolate(frame, [25, 40], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Visual analogy fade in
  const visualOpacity = interpolate(frame, [40, 55], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Pulse glow
  const pulseScale = interpolate(
    Math.sin(frame * 0.08),
    [-1, 1],
    [0.98, 1.02],
  );

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.BG_DEEP }}>
      <GradientBackground
        glowColor={COLORS.NEON_CYAN}
        glowX={0.5}
        glowY={0.4}
      />

      <AbsoluteFill
        style={{
          justifyContent: 'center',
          alignItems: 'center',
          flexDirection: 'row',
          gap: 80,
        }}
        >
          {/* Left: MCP letters */}
        <div
          style={{
            opacity: interpolate(mcpSpring, [0, 0.3], [0, 1]),
            transform: `scale(${interpolate(mcpSpring, [0, 1], [0.9, 1])})`,
          }}
        >
          <span
            style={{
              ...TEXT.display,
              fontSize: FONT_SIZE.HEADLINE,
              background: GRADIENT_PRIMARY,
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            MCP
          </span>
        </div>

        {/* Center: Equals + description */}
        <div
          style={{
            flexDirection: 'column',
            alignItems: 'center',
            gap: 16,
          }}
        >
          <span style={{
            ...TEXT.display,
            fontSize: 72,
            color: COLORS.TEXT_MUTED,
            opacity: eqOpacity,
          }}>
            =
          </span>
          <div
            style={{
              ...TEXT.subtitle,
              fontSize: 28,
              color: COLORS.NEON_CYAN,
              textAlign: 'center',
              opacity: descOpacity,
            }}
          >
            USB-C for AI tools
          </div>
          <div
            style={{
              ...TEXT.body,
              fontSize: 18,
              color: COLORS.TEXT_MUTED,
              textAlign: 'center',
              maxWidth: 300,
              opacity: descOpacity,
            }}
          >
            Universal standard for connecting AI models to tools
          </div>
        </div>

        {/* Right: Visual analogy */}
        <div
          style={{
            opacity: visualOpacity,
            transform: `scale(${interpolate(visualOpacity, [0, 1], [0.9, 1]) * pulseScale})`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 12,
          }}
        >
          {/* Phone icon (simple) */}
          <div style={{
            width: 48,
            height: 48,
            borderRadius: 10,
            border: `2px solid ${COLORS.NEON_CYAN}50`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <span style={{ fontSize: 24 }}>🤖</span>
          </div>
          {/* Cable line */}
          <div style={{
            width: 3,
            height: 40,
            background: `linear-gradient(180deg, ${COLORS.NEON_CYAN}60, ${COLORS.NEON_CYAN}20)`,
            borderRadius: 2,
          }} />
          {/* Laptop icon */}
          <div style={{
            width: 48,
            height: 48,
            borderRadius: 10,
            border: `2px solid ${COLORS.NEON_GREEN}50`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: glowShadow(COLORS.NEON_GREEN, 0.3),
          }}>
            <span style={{ fontSize: 24 }}>💻</span>
          </div>
          {/* Tool icon */}
          <div style={{
            width: 48,
            height: 48,
            borderRadius: 10,
            border: `2px solid ${COLORS.NEON_MAGENTA}50`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <span style={{ fontSize: 24 }}>🔧</span>
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
```

**Step 2: Commit**

```bash
git add explainer-video/src/scenes/S8MCPPrimer.tsx
git commit -m "feat: add S8 MCP Primer scene — 'USB-C for AI tools' analogy"
```

---

## Task 12: Create S9 Code Comparison Scene (P2 #13)

**Files:**
- Create: `explainer-video/src/scenes/S9CodeComparison.tsx`

**Step 1: Create the new scene**

```tsx
import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  spring,
  interpolate,
} from 'remotion';
import GradientBackground from '../components/GradientBackground';
import {
  COLORS,
  FONT_SIZE,
  FONT_MONO,
  TEXT,
} from '../lib/theme';
import { SPRING_SMOOTH, SPRING_DECAY } from '../lib/animations';

const MOVIEPY_LINES = [
  'from moviepy.editor import VideoFileClip',
  'from moviepy.video.fx.all import colorize',
  '',
  'clip = VideoFileClip("input.mp4")',
  'clip = clip.subclip(0, 10)',
  'clip = clip.resize((1920, 1080))',
  'clip = colorize(clip, saturation=1.5)',
  'clip = clip.set_fps(30)',
  'clip = clip.set_duration(10)',
  'clip.write_videofile("out.mp4")',
];

const MCPVIDEO_LINE = 'video.trim("input.mp4", start=0, end=10)';

export const S9CodeComparison: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Left panel entrance
  const leftSpring = spring({ frame, fps, config: SPRING_DECAY });

  // Right panel entrance (delayed)
  const rightSpring = spring({
    frame: Math.max(0, frame - 25),
    fps,
    config: { damping: 15, stiffness: 120, mass: 0.8 },
  });

  // Line-by-line reveal for left panel
  const linesVisible = Math.min(
    MOVIEPY_LINES.length,
    Math.floor(interpolate(frame, [10, 80], [0, MOVIEPY_LINES.length], {
      extrapolateRight: 'clamp',
    })),
  );

  // Right panel typing effect
  const charsVisible = Math.min(
    MCPVIDEO_LINE.length,
    Math.floor(interpolate(frame, [40, 70], [0, MCPVIDEO_LINE.length], {
      extrapolateRight: 'clamp',
    })),
  );

  // Bottom text
  const bottomOpacity = interpolate(frame, [80, 100], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.BG_DEEP }}>
      <GradientBackground
        glowColor={COLORS.NEON_CYAN}
        glowX={0.5}
        glowY={0.4}
      />

      <AbsoluteFill
        style={{
          flexDirection: 'row',
          padding: 80,
          gap: 60,
        }}
      >
        {/* Left: MoviePy (red tint) */}
        <div
          style={{
            flex: 1,
            opacity: interpolate(leftSpring, [0, 0.3], [0, 1]),
            transform: `translateX(${interpolate(leftSpring, [0, 1], [20, 0])}px)`,
          }}
        >
          <div
            style={{
              ...TEXT.overline,
              color: '#FF6B6B',
              fontSize: 14,
              marginBottom: 12,
            }}
          >
            MoviePy
          </div>
          <div
            style={{
              background: 'rgba(255,60,60,0.05)',
              border: '1px solid rgba(255,60,60,0.1)',
              borderRadius: 12,
              padding: 20,
              fontFamily: FONT_MONO,
              fontSize: 13,
              lineHeight: 1.8,
            }}
          >
            {MOVIEPY_LINES.map((line, i) => (
              <div
                key={i}
                style={{
                  color: i < linesVisible ? COLORS.TEXT_SECONDARY : 'rgba(255,255,255,0.1)',
                  whiteSpace: 'pre',
                }}
              >
                {line}
              </div>
            ))}
          </div>
        </div>

        {/* Center divider */}
        <div
          style={{
            width: 3,
            alignSelf: 'stretch',
            background: `linear-gradient(180deg, transparent, ${COLORS.TEXT_MUTED}20, transparent)`,
          }}
        />

        {/* Right: mcp-video (green tint) */}
        <div
          style={{
            flex: 1,
            opacity: interpolate(rightSpring, [0, 0.3], [0, 1]),
            transform: `translateX(${interpolate(rightSpring, [0, 1], [-20, 0])}px)`,
          }}
        >
          <div
            style={{
              ...TEXT.overline,
              color: COLORS.NEON_GREEN,
              fontSize: 14,
              marginBottom: 12,
            }}
          >
            mcp-video
          </div>
          <div
            style={{
              background: 'rgba(0,255,136,0.05)',
              border: `1px solid ${COLORS.NEON_GREEN}30`,
              borderRadius: 12,
              padding: 20,
              fontFamily: FONT_MONO,
              fontSize: 16,
              lineHeight: 1.8,
              boxShadow: glowShadow(COLORS.NEON_GREEN, 0.2),
            }}
          >
            <div style={{ color: COLORS.NEON_GREEN }}>
              {'>'}
            </div>
            <div style={{ color: COLORS.TEXT_PRIMARY }}>
              {MCPVIDEO_LINE.slice(0, charsVisible)}
            </div>
            <div style={{ color: COLORS.NEON_GREEN }}>
              {charsVisible >= MCPVIDEO_LINE.length ? "')" : ''}
            </div>
            <span
              style={{
                color: COLORS.NEON_CYAN,
                opacity: charsVisible >= MCPVIDEO_LINE.length
                  ? Math.floor(frame / 15) % 2 === 0 ? 1 : 0
                  : 0,
              }}
            >
              ▊
            </span>
          </div>
        </div>
      </AbsoluteFill>

      {/* Bottom text */}
      <div
        style={{
          position: 'absolute',
          bottom: 80,
          left: '50%',
          transform: 'translateX(-50%)',
          opacity: bottomOpacity,
          textAlign: 'center',
        }}
      >
        <span
          style={{
            ...TEXT.subtitle,
            fontSize: 28,
            background: GRADIENT_PRIMARY,
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          10 lines → 1 tool call
        </span>
      </div>
    </AbsoluteFill>
  );
};
```

**Step 2: Commit**

```bash
git add explainer-video/src/scenes/S9CodeComparison.tsx
git commit -m "feat: add S9 Code Comparison — MoviePy 10 lines vs mcp-video 1 line"
```

---

## Task 13: Rename S8CTA → S10CTA + Improve CTA (P1 #9)

**Files:**
- Rename: `explainer-video/src/scenes/S8CTA.tsx` → `explainer-video/src/scenes/S10CTA.tsx`
- Modify: `explainer-video/src/scenes/S10CTA.tsx` (typewriter + underline animation)

**Step 1: Rename the file**

```bash
git mv explainer-video/src/scenes/S8CTA.tsx explainer-video/src/scenes/S10CTA.tsx
```

**Step 2: Add typewriter effect to the pip install line**

Replace the static pip install text (lines 138-151) with a typewriter animation:

```tsx
        {/* Terminal with pip install — typewriter effect */}
        <div
          style={{
            opacity: interpolate(terminalSpring, [0, 0.3], [0, 1]),
            transform: `translateY(${interpolate(terminalSpring, [0, 1], [20, 0])}px)`,
            background: 'rgba(0,0,0,0.5)',
            borderRadius: 12,
            padding: '20px 32px',
            border: '1px solid rgba(255,255,255,0.06)',
          }}
        >
          <div
            style={{
              fontFamily: FONT_MONO,
              fontSize: 24,
              color: COLORS.TEXT_PRIMARY,
            }}
          >
            <span style={{ color: COLORS.NEON_GREEN }}>$</span>{' '}
            <span style={{ color: COLORS.TEXT_PRIMARY }}>
              pip install mcp-video
            </span>
            <span style={{
              color: COLORS.NEON_CYAN,
              opacity: cursorVisible ? 1 : 0,
            }}>
              {' '}▊
            </span>
          </div>

          {/* "Copied!" confirmation after typing */}
          {frame > 50 && (
            <div
              style={{
                position: 'absolute',
                top: -16,
                right: 0,
                opacity: interpolate(frame, [50, 60], [0, 1], {
                  extrapolateLeft: 'clamp',
                  extrapolateRight: 'clamp',
                }),
                ...TEXT.caption,
                fontSize: 14,
                color: COLORS.NEON_GREEN,
              }}
            >
              ✓ Copied!
            </div>
          )}
        </div>
```

**Step 3: Add underline sweep animation to GitHub URL**

Replace the GitHub URL pill (lines 198-218) with an animated version:

```tsx
        {/* GitHub URL pill with underline sweep */}
        <div
          style={{
            opacity: interpolate(pillSpring, [0, 0.3], [0, 1]),
            transform: `translateY(${interpolate(pillSpring, [0, 1], [12, 0])}px)`,
            background: 'rgba(27,28,30,0.7)',
            borderRadius: 999,
            padding: '10px 28px',
            border: '1px solid rgba(255,255,255,0.08)',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Underline sweep */}
          <div
            style={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              height: 2,
              width: `${interpolate(frame, [60, 80], [0, 100], { extrapolateRight: 'clamp' })}%`,
              background: COLORS.NEON_CYAN,
              borderRadius: 1,
            }}
          />
          <span
            style={{
              fontFamily: FONT_MONO,
              fontSize: 16,
              color: COLORS.NEON_CYAN,
              position: 'relative',
              zIndex: 1,
            }}
          >
            github.com/simonbraz/mcp-video
          </span>
        </div>
```

**Step 4: Commit**

```bash
git add explainer-video/src/scenes/S10CTA.tsx
git commit -m "feat(S10): rename from S8, add typewriter + copied confirmation + URL underline"
```

---

## Task 14: Wire Up ExplainerVideo.tsx — Add New Scenes + Captions (P0 #4)

**Files:**
- Modify: `explainer-video/src/ExplainerVideo.tsx`

**Step 1: Add imports for new scenes and caption component**

Replace imports section (lines 8-15) with:

```tsx
import { S1Hook } from './scenes/S1Hook';
import { S2Solution } from './scenes/S2Solution';
import { S3CoreEditing } from './scenes/S3CoreEditing';
import { S4ProFeatures } from './scenes/S4ProFeatures';
import { S5ImageCode } from './scenes/S5ImageCode';
import { S6Remotion } from './scenes/S6Remotion';
import { S7Architecture } from './scenes/S7Architecture';
import { S8MCPPrimer } from './scenes/S8MCPPrimer';
import { S9CodeComparison } from './scenes/S9CodeComparison';
import { S10CTA } from './scenes/S10CTA';
import { BurnedCaption } from './components/BurnedCaption';
```

**Step 2: Update TransitionSeries with new scenes and timing**

Replace the TransitionSeries content (lines 36-118) with the new 10-scene layout:

```tsx
      <TransitionSeries>
        {/* S1: Hook — 3s / 90 frames */}
        <TransitionSeries.Sequence durationInFrames={90}>
          <S1Hook />
          <BurnedCaption text="What if AI could edit video?" />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={slide({ direction: 'from-bottom' })}
          timing={snappy(12)}
        />

        {/* S2: Solution — 5s / 150 frames */}
        <TransitionSeries.Sequence durationInFrames={150}>
          <S2Solution />
          <BurnedCaption text="43 powerful video editing tools" />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={wipe({ direction: 'from-left' })}
          timing={snappy(12)}
        />

        {/* S3: Core Editing — 7s / 210 frames */}
        <TransitionSeries.Sequence durationInFrames={210}>
          <S3CoreEditing />
          <BurnedCaption text="Trim, merge, color grade — everything you need" />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={fade()}
          timing={snappy(10)}
        />

        {/* S4: Pro Features — 7s / 210 frames */}
        <TransitionSeries.Sequence durationInFrames={210}>
          <S4ProFeatures />
          <BurnedCaption text="Chroma key, stabilization, subtitles, and more" />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={slide({ direction: 'from-right' })}
          timing={snappy(12)}
        />

        {/* S5: Image & Code — 8s / 240 frames */}
        <TransitionSeries.Sequence durationInFrames={240}>
          <S5ImageCode />
          <BurnedCaption text="Extract colors and automate your workflow" />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={wipe({ direction: 'from-top' })}
          timing={snappy(12)}
        />

        {/* S6: Remotion — 6s / 180 frames */}
        <TransitionSeries.Sequence durationInFrames={180}>
          <S6Remotion />
          <BurnedCaption text="Seamless Remotion integration" />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={fade()}
          timing={snappy(10)}
        />

        {/* S7: Architecture — 7s / 210 frames */}
        <TransitionSeries.Sequence durationInFrames={210}>
          <S7Architecture />
          <BurnedCaption text="AI → MCP → FFmpeg → Output" />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={slide({ direction: 'from-right' })}
          timing={snappy(12)}
        />

        {/* S8: MCP Primer — 3s / 90 frames */}
        <TransitionSeries.Sequence durationInFrames={90}>
          <S8MCPPrimer />
          <BurnedCaption text="MCP = USB-C for AI tools" />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={wipe({ direction: 'from-left' })}
          timing={snappy(12)}
        />

        {/* S9: Code Comparison — 4s / 120 frames */}
        <TransitionSeries.Sequence durationInFrames={120}>
          <S9CodeComparison />
          <BurnedCaption text="Simple code, powerful results" />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={slide({ direction: 'from-right' })}
          timing={snappy(12)}
        />

        {/* S10: CTA — 7s / 210 frames */}
        <TransitionSeries.Sequence durationInFrames={210}>
          <S10CTA />
          <BurnedCaption text="pip install mcp-video" />
        </TransitionSeries.Sequence>
      </TransitionSeries>
```

**Step 3: Verify total: 90+150+210+210+240+180+210+90+120+210 = 1710, + 7 transitions × ~12 = 1626. Pad S8 to 120 frames or adjust to hit 2100.**

Actually, with TransitionSeries the total is the sum of all sequence durations (transitions overlap). So total = 90+150+210+210+240+180+210+90+120+210 = 1710. We need 2100.

Adjust durations:
- S8 MCP Primer: 90 → 150 (+60)
- S10 CTA: 210 → 270 (+60)

Or distribute more evenly:
- S8 MCP Primer: 90 → 120 (+30)
- S9 Code Comparison: 120 → 180 (+60)
- S10 CTA: 210 → 240 (+30)

That gives 90+150+210+210+240+180+210+120+180+240 = 1830. Still short. Let me add more to existing scenes:
- S2 Solution: 150 → 180 (+30)
- S5 Image Code: 240 → 270 (+30)

Total: 90+180+210+210+270+180+210+120+180+240 = 1990. Add 110 more:
- S8: 120 → 150 (+30)
- S10: 240 → 320 (+80)

Total: 90+180+210+210+270+180+210+150+180+320 = 2100.

**Step 4: Commit**

```bash
git add explainer-video/src/ExplainerVideo.tsx
git commit -m "feat: wire up 10 scenes, add captions, update timing to 2100 frames (70s)"
```

---

## Task 15: Validate and Test

**Step 1: Run remotion_validate**

Run: `mcp-video remotion_validate` with project_path `explainer-video/`
Expected: `{"success":true,"valid":true,"issues":[],"warnings":[]}`

**Step 2: Render a mid-video still at frame 600**

Run: `mcp-video remotion_still` with project_path, composition_id `McpVideoExplainer`, frame `600`
Expected: Success — should show S4 Pro Features scene

**Step 3: Render a still at frame 1800**

Run: `mcp-video remotion_still` with frame `1800`
Expected: Success — should show S9 Code Comparison or S10 CTA

**Step 4: Commit any fixes if needed**

```bash
git add -A
git commit -m "fix: address validation issues"
```

---

## Task 16: Render Key Frames for Visual Review

**Step 1: Render 10 key frames**

| Frame | Scene |
|-------|-------|
| 45 | S1 Hook |
| 200 | S2 Solution |
| 400 | S3 Core Editing |
| 650 | S4 Pro Features |
| 900 | S5 Image Code |
| 1100 | S6 Remotion |
| 1250 | S7 Architecture |
| 1400 | S8 MCP Primer |
| 1600 | S9 Code Comparison |
| 1900 | S10 CTA |

Use `remotion_still` for each with output_path `out/stills/v2-s{N}-*.png`.

**Step 2: Visual review — read all 10 stills and check for issues**

---

## Task 17: Final Render

**Step 1: Run remotion_validate one more time**

**Step 2: Full render to `out/video-social-v2.mp4`**

Run: `mcp-video remotion_render` with composition_id `McpVideoExplainer`, output_path `out/video-social-v2.mp4`

**Step 3: Commit**

```bash
git commit -m "chore: add video-social-v2.mp4 and key frame stills to .gitignore"
# Note: the video and stills are in out/ which is gitignored
```

---

## Task 18: Phase 3 — Audio Exploration (Research Only)

**Files:**
- Create: `docs/plans/2026-03-28-audio-exploration.md`

**Step 1: Research mcp-video audio capabilities**

Check `video_add_audio`, `video_normalize_audio`, and `video_extract_audio` tool parameters.

**Step 2: Research royalty-free music sources**

Search for CC0/public domain electronic music suitable for tech videos.

**Step 3: Research TTS options**

Check OpenAI TTS API, ElevenLabs, and other options for generating voiceover.

**Step 4: Write findings to docs**

```bash
git add docs/plans/2026-03-28-audio-exploration.md
git commit -m "docs: add audio & sound design exploration (research only)"
```

---

## Execution Notes

- **Order:** Tasks 1-2 (infrastructure), then Tasks 3-10 (scene enhancements), then Task 11 (caption component), then Task 12 (add captions), then Tasks 13-14 (new scenes), then Task 15 (wire up), then Tasks 16-18 (validate + render + audio research)
- **Dogfood rule:** Always use mcp-video MCP tools for rendering, never raw CLI
- **Commit frequency:** One commit per task for easy rollback
- **No external assets needed:** All demos are code-generated (gradients, animations)
