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
import { BurnedCaption } from './components/BurnedCaption';

import { fade } from './lib/fade';
import {
  FONT_BODY,
  COLORS,
  GOOGLE_FONTS_URL,
} from './lib/theme';

// Snappy transition timing — no more springTiming damping:200
const snappy = (frames = 12) => linearTiming({ durationInFrames: frames });

export const ExplainerVideo: React.FC = () => {
  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.BG_DEEP,
        fontFamily: FONT_BODY,
      }}
    >
      <link rel="stylesheet" href={GOOGLE_FONTS_URL} />
      <TransitionSeries>
        {/* S1: Hook — 3s / 90 frames */}
        <TransitionSeries.Sequence durationInFrames={90}>
          <S1Hook />
          <BurnedCaption text="What if AI could edit video?" />
        </TransitionSeries.Sequence>

        {/* S1→S2: slide from-bottom */}
        <TransitionSeries.Transition
          presentation={slide({ direction: 'from-bottom' })}
          timing={snappy(12)}
        />

        {/* S2: Solution — 6s / 180 frames */}
        <TransitionSeries.Sequence durationInFrames={180}>
          <S2Solution />
          <BurnedCaption text="43 powerful video editing tools" />
        </TransitionSeries.Sequence>

        {/* S2→S3: wipe from-left */}
        <TransitionSeries.Transition
          presentation={wipe({ direction: 'from-left' })}
          timing={snappy(12)}
        />

        {/* S3: Core Editing — 7s / 210 frames */}
        <TransitionSeries.Sequence durationInFrames={210}>
          <S3CoreEditing />
          <BurnedCaption text="Trim, merge, color grade — everything you need" />
        </TransitionSeries.Sequence>

        {/* S3→S4: fade with slight scale */}
        <TransitionSeries.Transition
          presentation={fade()}
          timing={snappy(10)}
        />

        {/* S4: Pro Features — 7s / 210 frames */}
        <TransitionSeries.Sequence durationInFrames={210}>
          <S4ProFeatures />
          <BurnedCaption text="Chroma key, stabilization, subtitles, and more" />
        </TransitionSeries.Sequence>

        {/* S4→S5: slide from-right */}
        <TransitionSeries.Transition
          presentation={slide({ direction: 'from-right' })}
          timing={snappy(12)}
        />

        {/* S5: Image & Code — 9s / 270 frames */}
        <TransitionSeries.Sequence durationInFrames={270}>
          <S5ImageCode />
          <BurnedCaption text="Extract colors and automate your workflow" />
        </TransitionSeries.Sequence>

        {/* S5→S6: wipe from-top */}
        <TransitionSeries.Transition
          presentation={wipe({ direction: 'from-top' })}
          timing={snappy(12)}
        />

        {/* S6: Remotion — 6s / 180 frames */}
        <TransitionSeries.Sequence durationInFrames={180}>
          <S6Remotion />
          <BurnedCaption text="Seamless Remotion integration" />
        </TransitionSeries.Sequence>

        {/* S6→S7: fade */}
        <TransitionSeries.Transition
          presentation={fade()}
          timing={snappy(10)}
        />

        {/* S7: Architecture — 7s / 210 frames */}
        <TransitionSeries.Sequence durationInFrames={210}>
          <S7Architecture />
          <BurnedCaption text="AI → MCP → FFmpeg → Output" />
        </TransitionSeries.Sequence>

        {/* S7→S8: slide from-right */}
        <TransitionSeries.Transition
          presentation={slide({ direction: 'from-right' })}
          timing={snappy(12)}
        />

        {/* S8: MCP Primer — 5s / 150 frames */}
        <TransitionSeries.Sequence durationInFrames={150}>
          <S8MCPPrimer />
          <BurnedCaption text="MCP = USB-C for AI tools" />
        </TransitionSeries.Sequence>

        {/* S8→S9: wipe from-left */}
        <TransitionSeries.Transition
          presentation={wipe({ direction: 'from-left' })}
          timing={snappy(12)}
        />

        {/* S9: Code Comparison — 6s / 180 frames */}
        <TransitionSeries.Sequence durationInFrames={180}>
          <S9CodeComparison />
          <BurnedCaption text="Simple code, powerful results" />
        </TransitionSeries.Sequence>

        {/* S9→S10: slide from-right */}
        <TransitionSeries.Transition
          presentation={slide({ direction: 'from-right' })}
          timing={snappy(12)}
        />

        {/* S10: CTA — ~10.7s / 320 frames */}
        <TransitionSeries.Sequence durationInFrames={320}>
          <S10CTA />
          <BurnedCaption text="pip install mcp-video" />
        </TransitionSeries.Sequence>
      </TransitionSeries>
    </AbsoluteFill>
  );
};
