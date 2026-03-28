import React from 'react';
import { COLORS } from '../lib/theme';
import ToolCard from './ToolCard';
import type { ToolInfo } from '../lib/types';

interface FeatureGridProps {
  tools: ToolInfo[];
  columns?: number;
  staggerDelay?: number;
}

const FeatureGrid: React.FC<FeatureGridProps> = ({
  tools,
  columns = 3,
  staggerDelay = 8,
}) => {
  const gridStyle: React.CSSProperties = {
    display: 'grid',
    gridTemplateColumns: `repeat(${columns}, 1fr)`,
    gap: 24,
  };

  return (
    <div style={gridStyle}>
      {tools.map((tool, index) => (
        <ToolCard
          key={tool.name}
          name={tool.name}
          icon={tool.icon}
          description={tool.description}
          delay={index * staggerDelay}
        />
      ))}
    </div>
  );
};

export default FeatureGrid;
