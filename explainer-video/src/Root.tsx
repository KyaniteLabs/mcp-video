import React from 'react';
import { Composition } from 'remotion';
import { ExplainerVideo } from './ExplainerVideo';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="McpVideoExplainer"
        component={ExplainerVideo}
        durationInFrames={1500}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
