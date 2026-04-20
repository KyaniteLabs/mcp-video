# TikTok Captioned Clip from Landscape Video

## Agent Prompt

Turn the landscape video at `/videos/interview_raw.mp4` into a vertical TikTok clip. The viral moment is around 3:20 to 3:50 where the speaker drops the key insight. I want it in 9:16 with animated captions, a speed ramp for dramatic effect, and background music.

Follow these steps in order:

### Step 1: Trim the viral moment

Use **video_trim** to extract 30 seconds starting at 3:20.
```
input_path: /videos/interview_raw.mp4
start: "3:20"
duration: "30"
output_path: /tmp/tiktok_raw_trim.mp4
```
We keep it under 30 seconds since that is the sweet spot for TikTok completion rates.

### Step 2: Resize to vertical 9:16

Use **video_resize** to reframe for TikTok's vertical format.
```
input_path: /tmp/tiktok_raw_trim.mp4
aspect_ratio: "9:16"
quality: high
output_path: /tmp/tiktok_vertical.mp4
```
9:16 is TikTok's native aspect ratio. The tool will handle center-cropping so the speaker stays in frame.

### Step 3: Add a speed ramp for drama

Use **video_speed** to slow down the key moment at the start, then speed back up. First, create a slow-motion opening at 0.75x for the first 8 seconds by splitting the clip.

Trim the opening:
```
input_path: /tmp/tiktok_vertical.mp4
start: "0"
duration: "8"
output_path: /tmp/tiktok_opening.mp4
```
Slow it down:
```
input_path: /tmp/tiktok_opening.mp4
factor: 0.75
output_path: /tmp/tiktok_slow_opening.mp4
```
Trim the rest:
```
input_path: /tmp/tiktok_vertical.mp4
start: "8"
output_path: /tmp/tiktok_rest.mp4
```
Slightly speed up the rest for energy:
```
input_path: /tmp/tiktok_rest.mp4
factor: 1.15
output_path: /tmp/tiktok_fast_rest.mp4
```
Merge the two parts:
```
clips:
  - /tmp/tiktok_slow_opening.mp4
  - /tmp/tiktok_fast_rest.mp4
transition: dissolve
transition_duration: 0.3
output_path: /tmp/tiktok_ramped.mp4
```
Speed ramping hooks the viewer with a dramatic slow opening then picks up pace to keep attention.

### Step 4: Transcribe and add animated captions

Use **video_ai_transcribe** to generate timed text.
```
input_path: /tmp/tiktok_ramped.mp4
model: base
output_srt: /tmp/tiktok_captions.srt
```

Then use **video_text_animated** to add word-by-word captions in TikTok style.
```
input_path: /tmp/tiktok_ramped.mp4
text: "The one thing nobody tells you about building a startup..."
animation: typewriter
font: Arial Black
size: 42
color: "#FFFFFF"
position: center
start: 0
duration: 5
output_path: /tmp/tiktok_captioned.mp4
```
For TikTok, bold white text with a typewriter or fade animation matches what performs well on the platform.

### Step 5: Add background music

Use **video_add_audio** to layer in trending-style background music at low volume so it does not compete with the speaker.
```
video_path: /tmp/tiktok_captioned.mp4
audio_path: /assets/upbeat_ambient.mp3
volume: 0.25
mix: true
fade_in: 1
fade_out: 2
start_time: 0
output_path: /tmp/tiktok_with_music.mp4
```
Mix at 0.25 so the music supports the mood without drowning the voice. Fade out at the end for a clean finish.

### Step 6: Apply color grading for TikTok

Use **video_color_grade** with a warm preset that pops on phone screens.
```
input_path: /tmp/tiktok_with_music.mp4
preset: warm
output_path: /tmp/tiktok_graded.mp4
```
Warm tones tend to perform better on TikTok -- they feel inviting and cinematic on small screens.

### Step 7: Add a hook text overlay at the top

Use **video_add_text** to place a hook question in the first 3 seconds.
```
input_path: /tmp/tiktok_graded.mp4
text: "Wait for it..."
position: top-center
size: 36
color: "#CCFF00"
start_time: 0
duration: 3
output_path: /tmp/tiktok_hook.mp4
```

### Step 8: Normalize audio and export

Final audio normalization and conversion for TikTok's recommended format.
```
input_path: /tmp/tiktok_hook.mp4
target_lufs: -14
output_path: /tmp/tiktok_final.mp4
```
-14 LUFS is ideal for TikTok which normalizes louder than YouTube.

Use **video_convert** as a final step to ensure proper format.
```
input_path: /tmp/tiktok_final.mp4
format: mp4
quality: high
output_path: /output/tiktok_clip.mp4
```

### Step 9: Verify quality

Run **video_quality_check** on the final output to confirm everything is clean.
```
input_path: /output/tiktok_clip.mp4
```
