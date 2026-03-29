import React from 'react';
import { AbsoluteFill } from 'remotion';
import { TransitionSeries } from '@remotion/transitions';
import { linearTiming } from '@remotion/transitions';
import { slide } from '@remotion/transitions/slide';
import { wipe } from '@remotion/transitions/wipe';

import { S11AIFeatures } from './scenes/S11AIFeatures';
import { S12Transitions } from './scenes/S12Transitions';
import { S13AudioSynthesis } from './scenes/S13AudioSynthesis';
import { S14VisualEffects } from './scenes/S14VisualEffects';
import { S15QualityGuardrails } from './scenes/S15QualityGuardrails';
import { BurnedCaption } from './components/BurnedCaption';
import { SceneSoundDesign } from './components/SoundDesign';

import { fade } from './lib/fade';
import {
  FONT_BODY,
  COLORS,
  GOOGLE_FONTS_URL,
} from './lib/theme';

const snappy = (frames = 12) => linearTiming({ durationInFrames: frames });

export const NewScenes: React.FC = () => {
  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.BG_DEEP,
        fontFamily: FONT_BODY,
      }}
    >
      <link rel="stylesheet" href={GOOGLE_FONTS_URL} />
      <TransitionSeries>
        {/* S11: AI Features — 6s / 180 frames */}
        <TransitionSeries.Sequence durationInFrames={180}>
          <S11AIFeatures />
          <BurnedCaption text="7 AI-powered features for intelligent editing" />
          <SceneSoundDesign sceneNumber={11} />
        </TransitionSeries.Sequence>

        {/* S11→S12: wipe from-right */}
        <TransitionSeries.Transition
          presentation={wipe({ direction: 'from-right' })}
          timing={snappy(12)}
        />

        {/* S12: Transitions — 6s / 180 frames */}
        <TransitionSeries.Sequence durationInFrames={180}>
          <S12Transitions />
          <BurnedCaption text="Cinematic transitions: slide, wipe, fade, cube" />
          <SceneSoundDesign sceneNumber={12} />
        </TransitionSeries.Sequence>

        {/* S12→S13: fade */}
        <TransitionSeries.Transition
          presentation={fade()}
          timing={snappy(10)}
        />

        {/* S13: Audio Synthesis — 6s / 180 frames */}
        <TransitionSeries.Sequence durationInFrames={180}>
          <S13AudioSynthesis />
          <BurnedCaption text="AI audio: speech synthesis, sound effects, stem separation" />
          <SceneSoundDesign sceneNumber={13} />
        </TransitionSeries.Sequence>

        {/* S13→S14: slide from-top */}
        <TransitionSeries.Transition
          presentation={slide({ direction: 'from-top' })}
          timing={snappy(12)}
        />

        {/* S14: Visual Effects — 6s / 180 frames */}
        <TransitionSeries.Sequence durationInFrames={180}>
          <S14VisualEffects />
          <BurnedCaption text="Pro VFX: particles, glow, chroma key, blur" />
          <SceneSoundDesign sceneNumber={14} />
        </TransitionSeries.Sequence>

        {/* S14→S15: wipe from-left */}
        <TransitionSeries.Transition
          presentation={wipe({ direction: 'from-left' })}
          timing={snappy(12)}
        />

        {/* S15: Quality Guardrails — 6s / 180 frames */}
        <TransitionSeries.Sequence durationInFrames={180}>
          <S15QualityGuardrails />
          <BurnedCaption text="Automated quality checks: brightness, contrast, saturation, audio" />
          <SceneSoundDesign sceneNumber={15} />
        </TransitionSeries.Sequence>
      </TransitionSeries>
    </AbsoluteFill>
  );
};
