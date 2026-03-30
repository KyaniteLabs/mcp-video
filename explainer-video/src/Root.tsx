import React from 'react';
import { Composition } from 'remotion';
import { ExplainerVideo } from './ExplainerVideo';
import { ExplainerVideoV1 } from './ExplainerVideoV1';
import { NewScenes } from './NewScenes';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* Original 70s explainer */}
      <Composition
        id="McpVideoExplainer"
        component={ExplainerVideo}
        durationInFrames={3062}
        fps={30}
        width={1920}
        height={1080}
      />
      
      {/* NEW v1.0 Extended 90s explainer */}
      <Composition
        id="McpVideoExplainerV1"
        component={ExplainerVideoV1}
        durationInFrames={3000}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{}}
      />
      
      {/* New scenes S11-S15 only (30s) */}
      <Composition
        id="NewScenes"
        component={NewScenes}
        durationInFrames={900}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
