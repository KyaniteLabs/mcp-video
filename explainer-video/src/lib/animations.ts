import { spring, interpolate, Easing, useCurrentFrame, useVideoConfig } from 'remotion';
import { AMBIENT } from './theme';

// ── Spring configs ─────────────────────────────────────────────
export const SPRING_SNAP = { damping: 200, stiffness: 200, mass: 0.5 };
export const SPRING_BOUNCE = { damping: 32, stiffness: 50, mass: 1.2 };
export const SPRING_SMOOTH = { damping: 40, stiffness: 60, mass: 1.2 };
export const SPRING_DECAY = { damping: 50, stiffness: 90, mass: 1.2 };
export const SPRING_SLAM = { damping: 12, stiffness: 200, mass: 0.8 };
export const SPRING_GLASS = { damping: 20, stiffness: 80, mass: 1.0 };

// ── Easing functions ───────────────────────────────────────────
export const EASE_OUT_EXPO = Easing.bezier(0.16, 1, 0.3, 1);
export const EASE_IN_OUT_QUART = Easing.bezier(0.76, 0, 0.24, 1);
export const EASE_OUT_BACK = Easing.bezier(0.34, 1.56, 0.64, 1);

// ── Ambient motion hook ────────────────────────────────────────
// Call once per scene for continuous subtle motion
export const useAmbientMotion = (frame?: number) => {
  const currentFrame = frame ?? useCurrentFrame();
  return {
    breathe: interpolate(
      Math.sin(currentFrame * 0.03),
      [-1, 1],
      [AMBIENT.BREATHE_MIN, AMBIENT.BREATHE_MAX],
    ),
    shimmer: Math.sin(currentFrame * AMBIENT.SHIMMER_SPEED),
    drift: Math.sin(currentFrame * AMBIENT.DRIFT_SPEED) * AMBIENT.DRIFT_AMPLITUDE,
  };
};

// ── Stagger helper ─────────────────────────────────────────────
export const stagger = (
  frame: number,
  index: number,
  delayFrames: number,
): number => Math.max(0, frame - index * delayFrames);

// ── Entrance animation ─────────────────────────────────────────
export const entrance = (
  frame: number,
  fps: number,
  delay = 0,
  config = SPRING_SMOOTH,
): { opacity: number; translateY: number; scale: number } => {
  const localFrame = Math.max(0, frame - delay);
  const sp = spring({
    frame: localFrame,
    fps,
    config,
  });
  return {
    opacity: interpolate(sp, [0, 1], [0, 1]),
    translateY: interpolate(sp, [0, 1], [16, 0]),
    scale: interpolate(sp, [0, 1], [0.96, 1]),
  };
};

// ── Oscillating glow intensity ─────────────────────────────────
export const glowPulse = (frame: number, speed = 0.05): number =>
  interpolate(Math.sin(frame * speed), [-1, 1], [0.3, 0.5]);

// ── Sine-wave vertical drift ───────────────────────────────────
export const floatingDrift = (
  frame: number,
  amplitude = 15,
  speed = 0.03,
): number => Math.sin(frame * speed) * amplitude;
