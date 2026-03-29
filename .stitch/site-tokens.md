# Raycast.com Design Tokens (extracted 2026-03-27)

Extracted via browser CSS analysis of https://raycast.com

## Colors (Dark Theme)

### Backgrounds
| Token | Hex | Source |
|-------|-----|--------|
| --grey-900 (BG base) | `#07080a` | body background |
| --grey-800 | `#0c0d0f` | |
| --grey-700 (BG elevated 1) | `#111214` | |
| --grey-600 (BG elevated 2) | `#1b1c1e` | |
| --grey-500 (BG elevated 3) | `#2f3031` | |
| --grey-400 | `#434345` | |
| --grey-300 | `#6a6b6c` | |
| --grey-200 | `#9c9c9d` | |
| --grey-100 | `#cdcece` | |
| --grey-50 | `#e6e6e6` | |
| --color-bg-100 | `rgb(16,17,17)` | `#101111` |
| --color-bg-200 | `rgb(24,25,26)` | `#18191a` |
| --color-bg-300 | `rgb(49,49,51)` | `#313133` |
| --color-bg-400 | `rgb(73,75,77)` | `#494b4d` |

### Text
| Token | Value | Source |
|-------|-------|--------|
| --color-fg (primary) | `hsl(240,11%,96%)` ~ `#f0f1f5` | |
| --color-fg-200 (secondary) | `rgb(194,199,202)` ~ `#c2c7ca` | |
| --color-fg-300 (muted) | `#78787c` | |
| --color-fg-400 (very muted) | `rgb(94,99,102)` ~ `#5e6366` | |

### Borders
| Token | Value |
|-------|-------|
| --color-border | `hsl(195,5%,15%)` ~ `#262829` |
| Card border (computed) | `rgba(255,255,255,0.06)` |
| Card border (hover) | `rgba(255,255,255,0.1)` |

### Accent Colors
| Token | Value |
|-------|-------|
| --color-blue | `hsl(202,100%,67%)` ~ `#56c2ff` |
| --color-green | `hsl(151,59%,59%)` ~ `#59d499` |
| --color-red | `hsl(0,100%,69%)` ~ `#ff6363` |
| --color-yellow | `hsl(43,100%,60%)` ~ `#ffc531` |

## Typography

### Font Families
- Display/Body: `Inter, "Inter Fallback", sans-serif`
- Monospace: `GeistMono, ui-monospace, SFMono-Regular, "Roboto Mono", Menlo, Monaco, monospace`
- (--monospace-font): `JetBrains Mono, Menlo, Monaco, Courier, monospace`

### Type Scale
| Element | Size | Weight | Letter-Spacing | Line-Height |
|---------|------|--------|---------------|-------------|
| h1 | 64px | 600 | normal | 1.1 (70.4px) |
| h3 | 24px | 500 | 0.2px | normal |
| h2 | 20px | 500 | 0.2px | normal |
| paragraph | 18px | 400 | 0.2px | normal |
| body | 16px | 400 | normal | 1.15 (18.4px) |
| small/caption | 14px | 400 | normal | normal |

### Weights Used
300 (light), 400 (regular), 500 (medium), 600 (semibold), 700 (bold)

## Spacing Scale

| Token | Value |
|-------|-------|
| --spacing-0-5 | 4px |
| --spacing-1 | 8px |
| --spacing-1-5 | 12px |
| --spacing-2 | 16px |
| --spacing-2-5 | 20px |
| --spacing-3 | 24px |
| --spacing-4 | 32px |
| --spacing-5 | 40px |
| --spacing-6 | 48px |
| --spacing-7 | 56px |
| --spacing-8 | 64px |
| --spacing-9 | 80px |
| --spacing-10 | 96px |
| --spacing-11 | 112px |
| --spacing-12 | 168px |
| --spacing-13 | 224px |

## Border Radius

| Token | Value |
|-------|-------|
| --rounding-xs | 4px |
| --rounding-sm | 6px |
| --rounding-normal | 8px |
| --rounding-md | 12px |
| --rounding-lg | 16px |
| --rounding-xl | 20px |
| --rounding-xxl | 24px |
| --rounding-full | 100% |
