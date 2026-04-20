import React, { useEffect, useRef } from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { soundDesign } from '../lib/sound-design';

interface SceneSoundDesignProps {
  sceneNumber: number;
}

export const SceneSoundDesign: React.FC<SceneSoundDesignProps> = ({ sceneNumber }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const initialized = useRef(false);
  const lastTrigger = useRef<Record<string, number>>({});

  useEffect(() => {
    if (!initialized.current) {
      soundDesign.init();
      
      // Scene-specific drone frequencies
      const droneFreqs: Record<number, number> = {
        1: 80,   // Hook - low mysterious
        2: 100,  // Solution - rising
        3: 120,  // Core editing - brighter
        4: 90,   // Pro features - deeper
        5: 110,  // Color analysis - active
        6: 130,  // Remotion - techy higher
        7: 85,   // Architecture - solid
        8: 105,  // MCP Primer - connection
        9: 125,  // Code comparison - intellectual
        10: 95,  // CTA - building to finish
        11: 115, // AI Features - bright
        12: 100, // Transitions - flowing
        13: 105, // Audio Synthesis - tonal
        14: 110, // Visual Effects - dramatic
        15: 90,  // Quality Guardrails - confident
      };
      
      soundDesign.startDrone(droneFreqs[sceneNumber] || 100);
      initialized.current = true;
    }
    
    return () => {
      // Don't stop on unmount - let it continue between scenes
    };
  }, [sceneNumber]);

  // Trigger sounds based on frame and scene
  useEffect(() => {
    const trigger = (key: string, action: () => void, cooldown: number = 10) => {
      const last = lastTrigger.current[key] || -Infinity;
      if (frame - last > cooldown) {
        action();
        lastTrigger.current[key] = frame;
      }
    };

    switch (sceneNumber) {
      case 1: // Hook
        // Logo slam at frame 30
        if (frame === 30) {
          soundDesign.playWhoosh(0.5, 'up');
          trigger('chime', () => soundDesign.playChime(), 30);
        }
        break;
        
      case 2: // Solution
        // Counting ticks - every 10 frames during count
        if (frame < 48 && frame % 10 === 0) {
          trigger('click', () => soundDesign.playClick('low'), 5);
        }
        break;
        
      case 3: // Core Editing
        // Feature card activations
        if (frame % 70 === 20) {
          trigger('blip', () => soundDesign.playBlip(600, 0.05), 15);
        }
        break;
        
      case 4: // Pro Features
        // Pulse wave on nodes
        if (frame % 15 === 0) {
          trigger('blip', () => soundDesign.playBlip(800 + Math.random() * 400, 0.03), 10);
        }
        break;
        
      case 5: // Color Analysis
        // Scan sound
        if (frame === 20) {
          soundDesign.playScan(1.5);
        }
        // Swatch pops
        if (frame > 40 && frame % 15 === 0) {
          trigger('blip', () => soundDesign.playBlip(1000, 0.04), 15);
        }
        break;
        
      case 6: // Remotion
        // Typing texture
        if (frame > 20 && frame < 80 && frame % 5 === 0) {
          trigger('type', () => soundDesign.playTyping(0.5), 3);
        }
        break;
        
      case 7: // Architecture
        // Data flow packets
        if (frame % 45 === 30) {
          trigger('whoosh', () => soundDesign.playWhoosh(0.3, 'up'), 20);
        }
        // Box glow chimes
        if (frame % 40 === 10) {
          trigger('blip', () => soundDesign.playBlip(500, 0.05), 20);
        }
        break;
        
      case 8: // MCP Primer
        // Connection snaps
        if (frame === 40) {
          soundDesign.playWhoosh(0.2, 'up');
          setTimeout(() => soundDesign.playChime(), 200);
        }
        break;
        
      case 9: // Code Comparison
        // Typing on mcp-video side
        if (frame > 40 && frame % 8 === 0) {
          trigger('type', () => soundDesign.playTyping(0.8), 5);
        }
        // Victory at end
        if (frame === 80) {
          soundDesign.playChime();
        }
        break;
        
      case 10: // CTA
        // Terminal typing
        if (frame > 25 && frame < 50 && frame % 4 === 0) {
          trigger('type', () => soundDesign.playTyping(1), 2);
        }
        // Copied success
        if (frame === 60) {
          soundDesign.playChime();
        }
        break;

      case 11: // AI Features
        // Feature card pops
        if (frame % 30 === 15) {
          trigger('blip', () => soundDesign.playBlip(700, 0.04), 15);
        }
        // Upscale reveal
        if (frame === 90) {
          soundDesign.playWhoosh(0.3, 'up');
        }
        break;

      case 12: // Transitions
        // Transition swoosh on each card
        if (frame % 40 === 20) {
          trigger('whoosh', () => soundDesign.playWhoosh(0.4, 'down'), 20);
        }
        break;

      case 13: // Audio Synthesis
        // Waveform bleeps
        if (frame % 20 === 10) {
          trigger('blip', () => soundDesign.playBlip(400 + (frame % 5) * 100, 0.03), 10);
        }
        break;

      case 14: // Visual Effects
        // Effect burst on cards
        if (frame % 35 === 15) {
          trigger('whoosh', () => soundDesign.playWhoosh(0.3, 'up'), 20);
          trigger('blip', () => soundDesign.playBlip(900, 0.04), 15);
        }
        break;

      case 15: // Quality Guardrails
        // Check chimes
        if (frame % 25 === 20) {
          trigger('chime', () => soundDesign.playChime(), 25);
        }
        // Final pass
        if (frame === 100) {
          soundDesign.playWhoosh(0.5, 'up');
        }
        break;
    }
  }, [frame, sceneNumber]);

  return null; // No visual output
};

// Global sound design initializer
export const GlobalSoundDesign: React.FC = () => {
  useEffect(() => {
    soundDesign.init();
    soundDesign.startDrone(80, 0.3);
    
    return () => {
      soundDesign.stop();
    };
  }, []);
  
  return null;
};
