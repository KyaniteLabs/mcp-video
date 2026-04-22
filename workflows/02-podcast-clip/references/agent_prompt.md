# Podcast Clip with Captions, Waveform, and Branded Intro/Outro

## Agent Prompt

Take the podcast episode at `/videos/podcast_ep42_full.mp4` and create a 60-second highlight clip. The best part starts at 12:34 and runs for about a minute where the guest explains their framework.

Here is my plan -- follow these steps in order:

### Step 1: Trim the highlight segment

Use **video_trim** to extract the section from 12:34 to 13:34.
```
input_path: /videos/podcast_ep42_full.mp4
start: "12:34"
duration: "60"
output_path: /tmp/podcast_raw_clip.mp4
```
This gives us the raw segment to work with before adding polish.

### Step 2: Extract and analyze the audio

Use **video_extract_audio** to pull the audio track so we can work with it separately.
```
input_path: /tmp/podcast_raw_clip.mp4
format: wav
output_path: /tmp/podcast_audio.wav
```
Then use **video_audio_waveform** to get the audio peaks. This helps us find the loudest moments for visual emphasis later.
```
input_path: /tmp/podcast_raw_clip.mp4
bins: 60
```

### Step 3: Normalize the audio levels

Podcast audio is often uneven. Use **video_normalize_audio** to bring everything to YouTube's recommended loudness.
```
input_path: /tmp/podcast_raw_clip.mp4
target_lufs: -16
output_path: /tmp/podcast_normalized.mp4
```
-16 LUFS is the sweet spot for social media -- loud enough to be clear but won't get squashed by platform compression.

### Step 4: Transcribe and generate captions

Use **video_ai_transcribe** to get the spoken text with timestamps.
```
input_path: /tmp/podcast_normalized.mp4
model: base
output_srt: /tmp/podcast_captions.srt
```

Then burn the captions into the video using **video_subtitles_styled** with a style that's easy to read.
```
input_path: /tmp/podcast_normalized.mp4
subtitles_path: /tmp/podcast_captions.srt
output_path: /tmp/podcast_captioned.mp4
style:
  font: Arial Black
  size: 24
  color: "#FFFFFF"
  outline_color: "#000000"
  outline_width: 2
  position: bottom
```

### Step 5: Add a branded intro card

Use **video_add_text** to overlay the show name at the top for the first 4 seconds.
```
input_path: /tmp/podcast_captioned.mp4
text: "The Build Podcast | Ep. 42"
position: top-center
size: 36
color: "#CCFF00"
start_time: 0
duration: 4
output_path: /tmp/podcast_with_intro.mp4
```

### Step 6: Add a branded outro card

Add a CTA text overlay at the end.
```
input_path: /tmp/podcast_with_intro.mp4
text: "Subscribe for new episodes every Tuesday"
position: center
size: 28
color: "#FFFFFF"
start_time: 55
duration: 5
output_path: /tmp/podcast_with_outro.mp4
```

### Step 7: Add the show logo as a watermark

Use **video_watermark** to place the logo in the corner throughout the clip.
```
input_path: /tmp/podcast_with_outro.mp4
image_path: /assets/build_podcast_logo.png
position: top-left
opacity: 0.6
margin: 15
output_path: /output/podcast_ep42_clip.mp4
```

### Step 8: Final quality check

Run **video_quality_check** on the output to make sure brightness, contrast, and audio levels are all within spec.
```
input_path: /output/podcast_ep42_clip.mp4
```

If anything flags, use **video_fix_design_issues** to auto-correct before publishing.
