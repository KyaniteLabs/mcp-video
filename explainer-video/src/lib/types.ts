import type { ReactNode } from 'react';

export interface ToolInfo {
  name: string;
  icon: string;
  description: string;
}

export interface SceneProps {
  // Optional per-scene overrides
}

export interface ColorInfo {
  hex: string;
  rgb: [number, number, number];
  cssName: string;
  percentage: number;
}

export interface SpringConfig {
  damping: number;
  stiffness: number;
  mass: number;
}

export interface LayerInfo {
  label: string;
  detail?: string;
}

export interface PipelineStep {
  label: string;
  icon?: string;
}

export interface OrbitItem {
  content: ReactNode;
}

export interface FloatingCardProps {
  title: string;
  body: string;
  accent?: string;
  delay?: number;
}

export interface TerminalLine {
  text: string;
  color?: string;
}
