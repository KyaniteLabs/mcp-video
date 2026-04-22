# Product Demo Video with Logo, Chapters, Transitions, and Color Grading

## Agent Prompt

Create a polished product demo video from the raw screen recordings and talking-head segments I have. The final video should have a branded intro, chapter markers for each feature section, smooth transitions, a logo watermark, and professional color grading.

Source files:
- Intro segment: `/raw/demo_intro.mp4`
- Feature 1 walkthrough: `/raw/feature_dashboard.mp4`
- Feature 2 walkthrough: `/raw/feature_analytics.mp4`
- Feature 3 walkthrough: `/raw/feature_export.mp4`
- Outro segment: `/raw/demo_outro.mp4`
- Company logo: `/assets/company_logo.png`

Follow these steps:

### Step 1: Trim and clean each segment

For each raw segment, trim to remove dead air at the start and end. Use **video_ai_remove_silence** on each file first to cut out any awkward pauses.
```
input_path: /raw/demo_intro.mp4
silence_threshold: -45
min_silence_duration: 1.0
keep_margin: 0.2
output_path: /tmp/intro_clean.mp4
```
Repeat for the other four segments, producing `feature1_clean.mp4`, `feature2_clean.mp4`, `feature3_clean.mp4`, and `outro_clean.mp4`. Removing silence keeps the demo tight and maintains viewer attention.

### Step 2: Normalize audio across all segments

Different recordings may have different levels. Normalize each to -16 LUFS (broadcast standard for web).
```
input_path: /tmp/intro_clean.mp4
target_lufs: -16
output_path: /tmp/intro_norm.mp4
```
Repeat for all segments. Consistent loudness prevents jarring level jumps between clips.

### Step 3: Merge with transitions

Use **video_merge** to combine all segments with professional transitions between each.
```
clips:
  - /tmp/intro_norm.mp4
  - /tmp/feature1_norm.mp4
  - /tmp/feature2_norm.mp4
  - /tmp/feature3_norm.mp4
  - /tmp/outro_norm.mp4
transitions:
  - dissolve
  - wipe-right
  - dissolve
  - fade
transition_duration: 0.8
output_path: /tmp/demo_merged.mp4
```
Varied transitions keep things visually interesting. Dissolves for talking segments, wipe-right for screen recordings to suggest moving between features, and a fade for the closing.

### Step 4: Add the logo watermark

Use **video_watermark** to place the company logo as a subtle but persistent brand element.
```
input_path: /tmp/demo_merged.mp4
image_path: /assets/company_logo.png
position: top-right
opacity: 0.5
margin: 20
output_path: /tmp/demo_branded.mp4
```
0.5 opacity keeps the logo visible without being distracting. Top-right is the standard position for demo videos since screen content is usually centered.

### Step 5: Add chapter title overlays

Use **video_add_text** to place chapter titles at the start of each feature section. You will need to know the timestamps from the merge step.

For the Dashboard feature (starting at the beginning of the first feature clip):
```
input_path: /tmp/demo_branded.mp4
text: "Dashboard Overview"
position: bottom-left
size: 32
color: "#CCFF00"
start_time: 15
duration: 4
output_path: /tmp/demo_ch1.mp4
```

For the Analytics feature:
```
input_path: /tmp/demo_ch1.mp4
text: "Analytics & Reporting"
position: bottom-left
size: 32
color: "#CCFF00"
start_time: 45
duration: 4
output_path: /tmp/demo_ch2.mp4
```

For the Export feature:
```
input_path: /tmp/demo_ch2.mp4
text: "Export & Integration"
position: bottom-left
size: 32
color: "#CCFF00"
start_time: 80
duration: 4
output_path: /tmp/demo_ch3.mp4
```
Chapter titles orient the viewer and make the demo scannable. The 4-second duration is long enough to read without blocking content.

### Step 6: Apply cinematic color grading

Use **video_filter** with `filter_type="color_preset"` and `params={"preset": "cinematic"}` for a professional, polished look.
```
input_path: /tmp/demo_ch3.mp4
preset: cinematic
output_path: /tmp/demo_graded.mp4
```
The cinematic preset adds subtle contrast and color richness that makes screen recordings look more intentional and branded.

### Step 7: Add fade in and fade out

Use **video_fade** for a clean opening and closing.
```
input_path: /tmp/demo_graded.mp4
fade_in: 1
fade_out: 2
output_path: /tmp/demo_faded.mp4
```
A 1-second fade in feels professional without wasting time. The 2-second fade out gives a graceful ending.

### Step 8: Detect scenes and generate chapter markers

Use **video_detect_scenes** to auto-detect scene boundaries for reference, then **video_auto_chapters** to generate chapter timestamps.
```
input_path: /tmp/demo_faded.mp4
threshold: 0.3
```
This gives you structured chapter data you can include in the video description on YouTube or Vimeo.

### Step 9: Final export with quality settings

Use **video_export** for the final render optimized for web hosting.
```
input_path: /tmp/demo_faded.mp4
format: mp4
quality: high
output_path: /output/product_demo_final.mp4
```

### Step 10: Quality verification

Run **video_quality_check** and **video_design_quality_check** on the final output.
```
input_path: /output/product_demo_final.mp4
```
This catches any remaining issues with brightness, contrast, audio clipping, or visual quality before you publish.
