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
import { S8CTA } from './scenes/S8CTA';

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
        </TransitionSeries.Sequence>

        {/* S1→S2: slide from-bottom */}
        <TransitionSeries.Transition
          presentation={slide({ direction: 'from-bottom' })}
          timing={snappy(12)}
        />

        {/* S2: Solution — 5s / 150 frames */}
        <TransitionSeries.Sequence durationInFrames={150}>
          <S2Solution />
        </TransitionSeries.Sequence>

        {/* S2→S3: wipe from-left */}
        <TransitionSeries.Transition
          presentation={wipe({ direction: 'from-left' })}
          timing={snappy(12)}
        />

        {/* S3: Core Editing — 7s / 210 frames */}
        <TransitionSeries.Sequence durationInFrames={210}>
          <S3CoreEditing />
        </TransitionSeries.Sequence>

        {/* S3→S4: fade with slight scale */}
        <TransitionSeries.Transition
          presentation={fade()}
          timing={snappy(10)}
        />

        {/* S4: Pro Features — 7s / 210 frames */}
        <TransitionSeries.Sequence durationInFrames={210}>
          <S4ProFeatures />
        </TransitionSeries.Sequence>

        {/* S4→S5: slide from-right */}
        <TransitionSeries.Transition
          presentation={slide({ direction: 'from-right' })}
          timing={snappy(12)}
        />

        {/* S5: Image & Code — 8s / 240 frames */}
        <TransitionSeries.Sequence durationInFrames={240}>
          <S5ImageCode />
        </TransitionSeries.Sequence>

        {/* S5→S6: wipe from-top */}
        <TransitionSeries.Transition
          presentation={wipe({ direction: 'from-top' })}
          timing={snappy(12)}
        />

        {/* S6: Remotion — 6s / 180 frames */}
        <TransitionSeries.Sequence durationInFrames={180}>
          <S6Remotion />
        </TransitionSeries.Sequence>

        {/* S6→S7: fade */}
        <TransitionSeries.Transition
          presentation={fade()}
          timing={snappy(10)}
        />

        {/* S7: Architecture — 7s / 210 frames */}
        <TransitionSeries.Sequence durationInFrames={210}>
          <S7Architecture />
        </TransitionSeries.Sequence>

        {/* S7→S8: slide from-right */}
        <TransitionSeries.Transition
          presentation={slide({ direction: 'from-right' })}
          timing={snappy(12)}
        />

        {/* S8: CTA — 7s / 210 frames */}
        <TransitionSeries.Sequence durationInFrames={210}>
          <S8CTA />
        </TransitionSeries.Sequence>
      </TransitionSeries>
    </AbsoluteFill>
  );
};
