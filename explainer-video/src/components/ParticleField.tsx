import React, { useMemo } from 'react';
import { AbsoluteFill, useCurrentFrame, interpolate } from 'remotion';
import { COLORS } from '../lib/theme';
import { stagger, floatingDrift } from '../lib/animations';

interface ParticleFieldProps {
  count?: number;
}

interface Particle {
  x: number;
  y: number;
  size: number;
  color: string;
  opacity: number;
  speed: number;
}

// Seeded pseudo-random using index * prime % 100 / 100 for determinism
const seededRandom = (index: number, prime: number): number =>
  ((index * prime) % 100) / 100;

const PARTICLE_COLORS = [COLORS.NEON_CYAN, COLORS.NEON_PURPLE];

const ParticleField: React.FC<ParticleFieldProps> = ({ count = 30 }) => {
  const frame = useCurrentFrame();

  const particles: Particle[] = useMemo(() => {
    return Array.from({ length: count }, (_, i) => ({
      x: seededRandom(i, 73) * 100,
      y: seededRandom(i, 137) * 100,
      size: 2 + seededRandom(i, 41) * 2, // 2-4px
      color: PARTICLE_COLORS[i % 2],
      opacity: 0.2 + seededRandom(i, 97) * 0.4, // 0.2-0.6
      speed: 0.5 + seededRandom(i, 59) * 1.5,
    }));
  }, [count]);

  return (
    <AbsoluteFill style={{ pointerEvents: 'none' }}>
      {particles.map((particle, i) => {
        const localFrame = stagger(frame, i, 1);
        const opacity = interpolate(localFrame, [20, 60], [0, particle.opacity], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });

        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: `calc(${particle.x}% + ${floatingDrift(frame, 15, 0.015 + i * 0.002)}px)`,
              top: `calc(${particle.y}% + ${floatingDrift(frame, 10, 0.02 + i * 0.003)}px)`,
              width: particle.size,
              height: particle.size,
              borderRadius: '50%',
              backgroundColor: particle.color,
              opacity,
              boxShadow: `0 0 ${particle.size}px ${particle.color}40`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

export default ParticleField;
