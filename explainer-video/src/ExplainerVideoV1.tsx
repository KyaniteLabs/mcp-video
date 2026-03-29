import React from 'react';
import { AbsoluteFill } from 'remotion';
import { TransitionSeries } from '@remotion/transitions';
import { linearTiming } from '@remotion/transitions';
import { slide } from '@remotion/transitions/slide';
import { wipe } from '@remotion/transitions/wipe';

import { S1Hook } from './scenes/S1Hook';
import { S2Solution } from './scenes/S2Solution';
import { S3CoreEditing } from './scenes/S3CoreEditing';
import { S4ProFeatures } from './scenes/S4ProFeatures';
import { S5ImageCode } from './scenes/S5ImageCode';
import { S6Remotion } from './scenes/S6Remotion';
import { S7Architecture } from './scenes/S7Architecture';
import { S8MCPPrimer } from './scenes/S8MCPPrimer';
import { S9CodeComparison } from './scenes/S9CodeComparison';
import { S10CTA } from './scenes/S10CTA';

// NEW v1.0 Scenes
import { S11AIFeatures } from './scenes/S11AIFeatures';
import { S12Transitions } from './scenes/S12Transitions';
import { S13AudioSynthesis } from './scenes/S13AudioSynthesis';
import { S14VisualEffects } from './scenes/S14VisualEffects';
import { S15QualityGuardrails } from './scenes/S15QualityGuardrails';

import { BurnedCaption } from './components/BurnedCaption';
import { GlobalSoundDesign, SceneSoundDesign } from './components/SoundDesign';

import { fade } from './lib/fade';
import {
  FONT_BODY,
  COLORS,
  GOOGLE_FONTS_URL,
} from './lib/theme';

// Snappy transition timing
const snappy = (frames = 12) => linearTiming({ durationInFrames: frames });

export const ExplainerVideoV1: React.FC = () => {
  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.BG_DEEP,
        fontFamily: FONT_BODY,
      }}
    >
      <link rel="stylesheet" href={GOOGLE_FONTS_URL} />
      <GlobalSoundDesign />
      <TransitionSeries>
        {/* S1: Hook — 3s / 90 frames */}
        <TransitionSeries.Sequence durationInFrames={90}>
          <S1Hook />
          <BurnedCaption text="What if AI could edit video?" />
          <SceneSoundDesign sceneNumber={1} />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={slide({ direction: 'from-bottom' })}
          timing={snappy(12)}
        />

        {/* S2: Solution — 6s / 180 frames */}
        <TransitionSeries.Sequence durationInFrames={180}>
          <S2Solution />
          <BurnedCaption text="79 powerful video editing tools" />
          <SceneSoundDesign sceneNumber={2} />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={wipe({ direction: 'from-left' })}
          timing={snappy(12)}
        />

        {/* S3: Core Editing — 7s / 210 frames */}
        <TransitionSeries.Sequence durationInFrames={210}>
          <S3CoreEditing />
          <BurnedCaption text="Trim, merge, color grade — everything you need" />
          <SceneSoundDesign sceneNumber={3} />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={fade()}
          timing={snappy(10)}
        />

        {/* S4: Pro Features — 7s / 210 frames */}
        <TransitionSeries.Sequence durationInFrames={210}>
          <S4ProFeatures />
          <BurnedCaption text="Chroma key, stabilization, subtitles, and more" />
          <SceneSoundDesign sceneNumber={4} />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={slide({ direction: 'from-right' })}
          timing={snappy(12)}
        />

        {/* S5: Image & Code — 9s / 270 frames */}
        <TransitionSeries.Sequence durationInFrames={270}>
          <S5ImageCode />
          <BurnedCaption text="Extract colors and automate your workflow" />
          <SceneSoundDesign sceneNumber={5} />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={wipe({ direction: 'from-top' })}
          timing={snappy(12)}
        />

        {/* S6: Remotion — 6s / 180 frames */}
        <TransitionSeries.Sequence durationInFrames={180}>
          <S6Remotion />
          <BurnedCaption text="Seamless Remotion integration" />
          <SceneSoundDesign sceneNumber={6} />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={fade()}
          timing={snappy(10)}
        />

        {/* S7: Architecture — 7s / 210 frames */}
        <TransitionSeries.Sequence durationInFrames={210}>
          <S7Architecture />
          <BurnedCaption text="AI → MCP → FFmpeg → Output" />
          <SceneSoundDesign sceneNumber={7} />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={slide({ direction: 'from-right' })}
          timing={snappy(12)}
        />

        {/* S8: MCP Primer — 5s / 150 frames */}
        <TransitionSeries.Sequence durationInFrames={150}>
          <S8MCPPrimer />
          <BurnedCaption text="MCP = USB-C for AI tools" />
          <SceneSoundDesign sceneNumber={8} />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={wipe({ direction: 'from-left' })}
          timing={snappy(12)}
        />

        {/* S9: Code Comparison — 6s / 180 frames */}
        <TransitionSeries.Sequence durationInFrames={180}>
          <S9CodeComparison />
          <BurnedCaption text="Simple code, powerful results" />
          <SceneSoundDesign sceneNumber={9} />
        </TransitionSeries.Sequence>

        {/* ============================
            NEW v1.0 FEATURES SECTIONS
            ============================ */}

        <TransitionSeries.Transition
          presentation={slide({ direction: 'from-bottom' })}
          timing={snappy(12)}
        />

        {/* S11: AI Features — 6s / 180 frames */}
        <TransitionSeries.Sequence durationInFrames={180}>
          <S11AIFeatures />
          <BurnedCaption text="7 AI-powered features for intelligent editing" />
          <SceneSoundDesign sceneNumber={11} />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={fade()}
          timing={snappy(10)}
        />

        {/* S12: Transitions — 5s / 150 frames */}
        <TransitionSeries.Sequence durationInFrames={150}>
          <S12Transitions />
          <BurnedCaption text="Glitch, pixelate, and morph transitions" />
          <SceneSoundDesign sceneNumber={12} />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={slide({ direction: 'from-right' })}
          timing={snappy(12)}
        />

        {/* S13: Audio Synthesis — 5s / 150 frames */}
        <TransitionSeries.Sequence durationInFrames={150}>
          <S13AudioSynthesis />
          <BurnedCaption text="Generate audio procedurally — no external files" />
          <SceneSoundDesign sceneNumber={13} />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={wipe({ direction: 'from-left' })}
          timing={snappy(12)}
        />

        {/* S14: Visual Effects — 5s / 150 frames */}
        <TransitionSeries.Sequence durationInFrames={150}>
          <S14VisualEffects />
          <BurnedCaption text="Vignette, chromatic aberration, scanlines, noise, glow" />
          <SceneSoundDesign sceneNumber={14} />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={fade()}
          timing={snappy(10)}
        />

        {/* S15: Quality Guardrails — 6s / 180 frames */}
        <TransitionSeries.Sequence durationInFrames={180}>
          <S15QualityGuardrails />
          <BurnedCaption text="Automated quality checks — linting for video" />
          <SceneSoundDesign sceneNumber={15} />
        </TransitionSeries.Sequence>

        <TransitionSeries.Transition
          presentation={slide({ direction: 'from-bottom' })}
          timing={snappy(12)}
        />

        {/* S10: CTA — ~10.7s / 320 frames */}
        <TransitionSeries.Sequence durationInFrames={320}>
          <S10CTA />
          <BurnedCaption text="pip install mcp-video" />
          <SceneSoundDesign sceneNumber={10} />
        </TransitionSeries.Sequence>
      </TransitionSeries>
    </AbsoluteFill>
  );
};
