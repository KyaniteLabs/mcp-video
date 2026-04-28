# Workflows — Routing Table

## Which workflow should I use?

| Goal | Workflow | Stages | Typical Duration |
|---|---|---|---|
| Turn a long video into a TikTok / Short / Reel | `01-social-media-clip` | 5 | 2-5 min |
| Extract a podcast highlight with chapters and captions | `02-podcast-clip` | 6 | 5-10 min |
| Build a branded explainer video from scratch | `03-explainer-video` | 7 | 30-60 min |
| Create a video with Hyperframes, then post-process | `04-hyperframes-video` | 5 | 10-20 min |

## How to run a workflow

1. `cd workflows/01-social-media-clip`
2. Read `CONTEXT.md` for the stage contract
3. Run `python workflow.py` (or follow the agent prompts in `references/`)
4. Review output at each stage before proceeding
5. Final artifact lands in `output/`

## Workflow structure

Each workflow follows ICM conventions:

- `CONTEXT.md` — Stage contract (Inputs, Process, Outputs)
- `references/` — Factory configuration (platform specs, style guides)
- `output/` — Working artifacts (generated at each stage)
- `workflow.py` — Runnable Python script using the mcp-video client
