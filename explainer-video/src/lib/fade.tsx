import React from 'react';
import type { TransitionPresentation, TransitionPresentationComponentProps } from '@remotion/transitions';

type FadeProps = Record<string, unknown>;

const FadePresentation: React.FC<TransitionPresentationComponentProps<FadeProps>> = ({
  children,
  presentationDirection,
  presentationProgress,
}) => {
  const opacity =
    presentationDirection === 'entering'
      ? presentationProgress
      : 1 - presentationProgress;

  return <div style={{ opacity, width: '100%', height: '100%' }}>{children}</div>;
};

export const fade = (): TransitionPresentation<FadeProps> => ({
  component: FadePresentation,
  props: {},
});
