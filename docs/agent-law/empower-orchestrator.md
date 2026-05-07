# Empower Orchestrator Agent Law

This repo-local copy makes the doctrine visible to Codex, Claude Code, Kimi Code, GitHub reviewers, and CI. It preserves the four-question blast-radius check as an explicit gate before automation or durable system changes.

Canonical installation source on this machine: `/Users/simongonzalezdecruz/Downloads/2026-05-04-empower-orchestrator-recipe.md`.

Repository: `KyaniteLabs/mcp-video`.

---

# Empower the Orchestrator, a recipe

A self-contained blueprint for installing this pattern in your own agent setup. If you run Claude Code, the Codex CLI, Cursor, or any harness where you talk to one agent and dispatch background workers, you can build this. Adapt the names and paths to whatever your stack calls them.

## The thesis (in one sentence)

**Every agent session is an audition to extend the system, not just complete a task.**

Most sessions today complete one-off work and die. The same patterns get re-solved by hand every time. Strong reasoning gets lost. The system gets no smarter over time.

The fix is a mindset shift you install in the orchestrator, plus four small commands.

> "Don't just do the task. Build the workflow that does this task and every future one like it."

When the orchestrator notices a repeated pattern (a task done 3+ times) or a recurring agent failure mode, it dispatches a worker to ship a permanent piece of infrastructure. Future sessions inherit it. The system gets smarter on every loop.

The success-state UX is one line, surfaced back in chat:

> *"I noticed X, found a better way. The system just got an upgrade."*

That line is the slogan and the user-facing payload of every successful audition.

---

## Part 1, the doctrine (paste this into your project memory)

This is the rule the orchestrator reads on every session start. Save it as a memory entry, a `CLAUDE.md` section, an `AGENTS.md` rule, or whatever your harness calls always-loaded context.

### The discipline

You are auditioning. Not to be re-summoned, to **leave inheritance behind**. Sharp sessions ship a tool, a doctrine doc, or a guardrail into the permanent system. Weak ones complete the task and die.

This applies to **any non-dispatch session, regardless of which model is in the seat** (Opus, Sonnet, Codex, Haiku, etc). Background workers do not audition. They execute. Only the top-level / orchestrator session carries the discipline.

### Two trigger classes

Either fires:

1. **Repeatable task.** "I'm about to do this thing for the Nth time." Dispatch a tool.
2. **Repeatable agent failure.** "Codex / Sonnet / model X keeps making this same mistake." Ship a guardrail (a memory entry, a brief addendum, or a hook).

Both prevent future friction. Tools attack work-volume. Guardrails attack agent-error-volume.

### The 4-question blast-radius check

Before invoking `/empower`, run this OUT LOUD in chat. Each question gets a green / yellow / red verdict.

| # | Question | Green | Yellow | Red |
|---|---|---|---|---|
| 1 | **Scale.** How many things does this touch when wrong? | One file, one workspace | Multi-file, single workspace | Cross-workspace, all sessions, or core config |
| 2 | **Severity.** What breaks if it ships wrong? | Minor friction (typo, awkward phrasing) | Broken workflow until reverted | Data loss, broken pipeline, system-wide harm, leaked content |
| 3 | **Reversibility.** How clean is the undo? | Single revert plus trash move | Revert plus manual cleanup | Surgery (external service call already fired) |
| 4 | **Predictability.** Can you articulate the failure mode in one sentence? | Yes, and it's bounded | Yes, but you're guessing | No, can't predict |

### Mode rules

- **All four green** → `--auto` permitted. The reversibility safety net is enough.
- **Any yellow** → **inline approval required.** Human sees the diff before merge.
- **Any red** → **DO NOT dispatch.** Either do the task inline (no automation yet), or escalate.

`/empower --auto` MUST refuse to dispatch unless the assessment is stated in chat immediately preceding the slash command. The slash command should only pass `--blast-radius-stated` after the orchestrator has written the assessment out loud. Forces the discipline. Removes the lazy `--auto` failure mode.

### What gets shipped

| Artifact | Where it lands | Discovery |
|---|---|---|
| Tool (executable) | `tools/<name>` (or your equivalent) | A `tools/CATALOG.md` listing |
| Skill | Your harness's auto-discovered skills dir | Auto-discovered |
| Slash command | Your harness's commands dir | Autocomplete |
| Sub-agent | Your harness's agents dir | Auto-discovered |
| Hook | Your harness's settings file | Fires automatically per event |
| Memory entry | Your project memory dir | Always loaded |
| Doctrine doc | A long-form `docs/` location | Pointer from a memory entry |
| Per-model guardrail | A loadable warning file (per executor) | Dispatcher appends to outgoing brief |

The principle: each artifact type uses its native discovery surface in your stack. Don't invent one shared catalog for everything.

---

## Part 2, the mechanism (the auto-upgrading system)

A worktree-isolated build with a green-light gate. Five moving parts on top of whatever dispatcher you already have.

### Flow

```
Orchestrator notices pattern
    │
    │ Reads doctrine, runs 4-question check, picks mode
    │
    ▼
/empower "<intent>" [--auto] [--type <kind>] [--executor <name>]
    │  Creates an isolated working copy (git worktree, branch, sandbox)
    │  Scaffolds a brief: target path, worker discipline, registration step
    │
    ▼
Background dispatcher
    │  Loads guardrails/<executor> addendum, appends to brief
    │  Dispatches worker into the isolated copy
    │
    ▼
Worker (any model, runs in isolation)
    │  Builds artifact, ships to canonical path,
    │  registers per the discovery matrix above, exits
    │
    ▼
                                   ┌─ Mode A (inline) ─────────────┐
   Worker exit notification ──────>│ Human: /ship-empower <id>     │
                                   └────────────┬──────────────────┘
                                                │
   ┌─ Mode B (--auto, all-green check) ────────┘
   │
   ▼
Ship step
    │  Merge isolated copy into main system (one commit per artifact)
    │  Append entry to tools/CATALOG.md
    │  Delete the isolated copy
    │  Surface: "I noticed X, found a better way. The system just got an upgrade."
    │           "Reversible: /revert-empower <id>"
    │
    ▼
[Future sessions inherit via auto-discovery + CATALOG load]
```

### Required worker discipline (BAKED INTO EVERY BRIEF)

Whatever `/empower` writes to the worker, it must include these rules:

1. **One artifact = one commit.** If the brief asks for 3 files, that's 3 commits. The reversibility design depends on this.
2. **Commit message format:** `empower(<artifact-type>): <one-line purpose>`
3. **CATALOG append goes IN the artifact's commit** (only for tool-type artifacts). After creating the tool, append a one-line entry to `tools/CATALOG.md`, then commit both files together.
4. **Stay inside the isolated copy.** Never write outside the working dir.
5. **Verify before committing.** For Python: `python3 -c "import ast; ast.parse(open('<path>').read())"`. For shell: `bash -n <path>`. For markdown: confirm non-empty.
6. **Exit cleanly.** Don't merge or push. The orchestrator handles the ship step.

---

## Part 3, the four commands

Each command is a markdown file in your harness's slash-command dir, invoking a small Python (or whatever) helper. Names are suggestions. Adapt to your conventions.

### `/empower "<intent>" --type <kind> --executor <name> [--auto] [--force]`

The entry point. The orchestrator invokes this when it spots a pattern.

**What the command does:**

1. **Refuses if `--auto` was passed without a prior 4-question assessment in chat.**
2. Greps `tools/CATALOG.md` for similar entries (token-overlap heuristic, not just substring). If hits, warns inline with candidates and asks for `--force` to proceed.
3. Slugifies the intent. Builds a worker ID like `w-<hash>-<date>-empower-<slug>`.
4. Creates an isolated working copy (git worktree off main) at a known path, on a new branch.
5. Composes the brief with: intent, target path, worker discipline rules, registration step, staging dir for non-repo artifacts (memory entries live outside the repo, so they need a staging area).
6. Dispatches: `your_dispatcher start --executor <name> --task-file <brief> --cwd <isolated-copy> --label empower-<slug>`.
7. Returns one-line confirmation: worker ID, isolated-copy path, target path, mode hint.
8. Continues main work. Notification fires when worker exits.

### `/ship-empower <worker_id>`

Inline-mode green-light. Merges the worker's isolated copy into main, prints the upgrade line, removes the copy.

**What the command does:**

1. Looks up the worker in the registry.
2. Verifies it exited cleanly (status = exited, exit_code = 0). Errors out if not.
3. Diffs the worker's branch against main to find shipped artifacts.
4. `git merge --ff-only <worker-branch>` into main. Errors if non-fast-forwardable.
5. Removes the isolated copy.
6. Prints: `"The system just got an upgrade: tools/<artifact>. Reversible: /revert-empower <worker_id>."`

### `/kill-empower <worker_id> [reason]`

Pre-ship discard. The worker built something but you don't want it.

**What the command does:**

1. If the worker process is still running, SIGTERMs it.
2. Removes the isolated copy with `git worktree remove --force` (the worker may have uncommitted state we're discarding).
3. Appends the rejection (worker ID + reason) to a `rejections.log` file so the nightly sweep doesn't re-propose the same idea.

### `/revert-empower <worker_id> [--file <path>]`

Post-ship undo. Works in either mode. The reversibility floor.

**What the command does:**

1. Walks the last N main commits looking for `empower(...)` subjects, optionally scoped by worker ID.
2. For each matching commit:
   - Copies the artifact files to `.empower-trash/<worker_id>/` (don't delete, keep recoverable).
   - Runs `git revert --no-edit <commit>` (inverse commit, history-preserving, never `git reset`).
3. Removes CATALOG entries (they were committed atomically with the artifact, so the revert handles them).
4. Logs the revert with timestamp.

**Optional `--file <path>`** scopes to a single artifact when the worker shipped multiple.

---

## Part 4, the reversibility floor (non-negotiable)

The reason `--auto` mode is acceptable is the undo button. Without this floor, `--auto` is reckless.

- Every ship lands as **exactly one isolated commit per artifact file** on main. A worker that produces 3 artifacts equals 3 commits.
- The CATALOG line for an artifact piggybacks on that artifact's commit (not a separate commit), so revert is atomic.
- Reverts are `git revert` (inverse commits), never history rewrites.
- Reverted files are MOVED to `.empower-trash/<worker_id>/`, never deleted. Recoverable for at least 30 days.
- Every revert is logged with timestamp and reason.

---

## Part 5, per-model guardrails (the second-order superpower)

Workers run on different models. Different models have different failure modes. Capture each one as you see it.

For every model you dispatch to, keep a small markdown file at `tools/dispatch_lib/guardrails/<model>.md` listing the warnings you've learned the hard way. The dispatcher appends the relevant file to every outgoing brief based on the `--executor` flag.

Example seed entries:

- **Codex.md**: "Use cwd-relative paths only, never absolute. Validate file existence after every write claim. Sub-repos need their own branching."
- **Sonnet.md**: "Stay in scope. No backwards-compat shims unless asked. Voice rules apply for brand-facing output."
- **MiniMax.md**: "Validate every claimed file write (we've seen success reports on writes that didn't happen). Don't fabricate partial progress."

When you discover a new failure mode, you `/empower` a guardrail update. The system gets smarter at routing around its own weak spots.

---

## Part 6, adaptation notes

Translating this to your setup:

- **No git worktrees?** Use a separate clone, a sandboxed branch, a Docker container, or a tmpdir snapshot. The point is isolation between build and main.
- **Different commands dir?** Whatever your harness auto-discovers is fine. Make the names match your other commands.
- **No background dispatcher?** This pattern still works with foreground subagents (the agent waits for the worker), it just costs more orchestrator tokens. Background is the optimization, not the requirement.
- **Different doctrine surface?** `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, a memory file, a system prompt prefix. Anywhere always-loaded works.
- **Different artifact discovery?** Map each artifact type to YOUR stack's native discovery surface. The matrix in Part 1 is suggestions, not gospel.

---

## Part 7, the slogan, again

Print this on every successful ship. It's the user-facing payload of the entire system.

> **"I noticed X, found a better way. The system just got an upgrade."**

When that line lands in chat, the agent has earned its session. //
