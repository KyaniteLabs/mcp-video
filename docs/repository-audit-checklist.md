# Repository Audit Checklist (Step-by-Step)

Use this checklist to keep `mcp-video` at professional quality across code, docs, CI/CD, GitHub setup, and growth readiness.

## 1) Code health (weekly)

1. Run lint + formatting checks.
2. Run non-slow tests locally.
3. Validate package build and artifact surface.
4. Review recently touched modules for consistency with `CONTRIBUTING.md` conventions.

Suggested commands:

```bash
ruff check mcp_video/
ruff format --check mcp_video/
pytest tests/ -q -m "not slow" --tb=short
python -m build --sdist --wheel
python .github/scripts/check-built-artifacts.py dist
```

## 2) Git hygiene (before every PR)

1. Ensure branch has an upstream.
2. Ensure working tree is clean before review handoff.
3. Prune stale remotes.
4. Run the Git audit script.

```bash
git fetch --prune origin
./scripts/git-professional-audit.sh
```

## 3) Repository readiness (before releases)

Run:

```bash
./scripts/repo-readiness-audit.py
```

This validates:
- core community files exist
- issue/PR templates exist
- workflow files exist
- README has key user onboarding sections
- package metadata URLs exist
- local tag visibility (release hygiene signal)

## 4) Documentation quality (weekly)

- README: accurate tool counts, install instructions, and quick-start snippets.
- Changelog/release notes: user-facing changes clearly summarized.
- Security/support docs: present and linked from README.
- Contributing docs: match real CI expectations.

## 5) GitHub setup (monthly)

- Branch protection on `master` is enabled.
- Required status checks include CI.
- Signed tags are used for releases when possible.
- Discussions/Issues templates route users to the right channel.
- GitHub Pages deployment remains intentional and artifact-safe.

## 6) Growth and accessibility (monthly)

- Keep issue templates concise and newcomer-friendly.
- Maintain a clear support path for questions.
- Ensure docs are scannable (headings, short paragraphs, command blocks).
- Prioritize fast “time to first success” in README.

## 7) Success metrics to track

- Time-to-first-success for new users.
- Issue response time.
- PR merge lead time.
- Release cadence consistency.
- Test pass rate stability.

Treat this as a living checklist: tighten checks whenever recurring problems appear.
