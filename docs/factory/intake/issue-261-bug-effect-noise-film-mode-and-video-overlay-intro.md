        # Factory intake for issue #261: Bug: effect_noise film mode and video_overlay introduce severe green color cast

        Repository: `KyaniteLabs/mcp-video`
        Category: `llm_fix`
        Source issue: `#261`

        ## User request

        ## Bug Report

Two mcp-video effects introduce a severe green color cast that shifts the entire image palette and makes rendered output unusable for production.

This was found while dogfooding mcp-video on the Mac Mini for the EP01 social teaser workflow.

### Affected tools

- `effect_noise` in `film` mode
- `video_overlay` blend mode

### 1. `effect_noise` in `film` mode

When applying film grain noise, the entire image shifts green. Frame-by-frame color analysis showed a major channel imbalance.

Before noise, after chromatic aberration output:

```text
Avg RGB: R=106.4, G=98.0, B=102.1
```

After `effect_noise` with film mode:

```text
Avg RGB: R=52.8, G=159.4, B=47.1
```

Parameters used:

```python
effect_noise(input_path, intensity=0.03, mode="film", animated=True)
```

### 2. `video_overlay` blend mode

When overlaying two videos at 50% opacity, the result shifts green.

Before overlay, background:

```text
Avg RGB: R=106.4, G=98.0, B=102.1
```

After overlay, 50% opacity center position:

```text
Avg RGB: R=75.9, G=138.3, B=67.2
```

Parameters used:

```python
video_overlay(background_path, overlay_path, opacity=0.5, position="center")
```

### Expected behavior

- Film grain should add luminance/noise texture without shifting chrominance.
- Overlay blend should composite without introducing a systematic green channel bias.

### Actual behavior

- `effect_noise` produces a strong green spike and crushes red/blue channels.
- `video_overlay` introduces a visible green bias across the whole frame.
- Output becomes unusable for color-sensitive production work.

### Workaround used during dogfood

- Skip `effect_noise` and use ffmpeg directly, for example `noise=alls=5`.
- Skip `video_overlay` blend and use ffmpeg overlay/blend filters directly.
- In the EP01 teaser workflow, the safe render path used only ffmpeg crop/eq/rgbashift/chromashift/vignette/drawtext/audio filters.

### Environment

- Machine: user's Mac Mini
- macOS Darwin 25.4.0
- ffmpeg 8.0 via Homebrew
- mcp-video latest at time of dogfood
- Tested on 1080x1920 vertical H.264 social video

        ## Factory interpretation

        This issue was picked up by `issue-closer`, but no safe code edit was
        produced by the configured agent providers. The Factory is therefore
        converting the issue into an implementation contract instead of silently
        skipping it.

        ## Acceptance contract

        - Confirm the desired behavior from the issue title and body.
        - Identify the smallest implementation slice that can ship independently.
        - Add or update tests/proofs for that slice before merging implementation.
        - Keep credentials, local machine paths, and deployment secrets out of the repo.
        - Close or update the source issue when the implementation PR lands.

        ## Next Factory action

        Dispatch a repo worker against this contract. If the request is too broad,
        split it into smaller `agent-ready` issues with concrete acceptance checks.
