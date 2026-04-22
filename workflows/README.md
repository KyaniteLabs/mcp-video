# mcp-video Workflows

ICM-style staged pipelines for common video productions.

## Available Workflows

| Workflow | Description | Stages |
|---|---|---|
| `01-social-media-clip` | Turn landscape video into TikTok / Short / Reel | 5 |
| `02-podcast-clip` | Extract highlight with chapters and captions | 6 |
| `03-explainer-video` | Build branded explainer from scratch | 7 |

## How to use

### With Claude Code

1. `cd workflows/01-social-media-clip`
2. Read `CONTEXT.md` to understand the pipeline
3. Place your raw video in the workflow directory
4. Run `python workflow.py /path/to/video.mp4`
5. Review `output/` at each stage

### As a human

Each workflow has:
- `CONTEXT.md` — Stage contract with Inputs, Process, Outputs
- `references/` — Factory configuration (specs, styles, presets)
- `workflow.py` — Runnable Python script
- `output/` — Generated artifacts

## Adding a new workflow

1. Create `workflows/NN-your-workflow/`
2. Write `CONTEXT.md` with stage contract
3. Add `references/` for configuration
4. Write `workflow.py` using the mcp-video client
5. Update `workflows/CONTEXT.md` routing table
