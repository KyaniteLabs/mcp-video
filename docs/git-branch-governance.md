# Git & Branch Governance (Professional Baseline)

This repo uses a simple, auditable Git workflow designed to minimize "branch mess" and integration surprises.

## 1) Branch standards

- Keep `master` releasable.
- Do work in short-lived branches named with purpose:
  - `feature/<topic>`
  - `fix/<topic>`
  - `chore/<topic>`
- Avoid committing directly to `master`.

## 2) Upstream discipline

Every local branch should track a remote branch.

```bash
git push -u origin <branch-name>
```

Benefits:
- Enables ahead/behind visibility.
- Makes rebasing and pull requests predictable.
- Prevents "orphan" local branches that cannot be reviewed.

## 3) Clean history habits

Before opening a PR:

1. `git fetch --prune`
2. Rebase your branch onto latest `origin/master`.
3. Resolve conflicts locally.
4. Ensure branch has no unrelated commits.

Suggested command sequence:

```bash
git fetch --prune origin
git rebase origin/master
```

## 4) Hygiene checks (required before PR)

Run:

```bash
./scripts/git-professional-audit.sh
```

The audit checks:
- detached HEAD state
- clean vs dirty working tree
- upstream tracking present
- ahead/behind/divergence status
- repository integrity (`git fsck --full`)
- stale tracking branches (`: gone]`)
- `init.defaultBranch` configuration

## 5) Routine cleanup

Weekly or before release:

```bash
./scripts/git-workspace-cleanup.sh
```

Manual equivalent:

```bash
git fetch --all --prune
git remote prune origin
git worktree prune
git branch --merged master
```

Delete fully merged local branches you no longer need:

```bash
git branch -d <branch-name>
```

## 6) Team guardrails

Repository settings should enforce:
- Pull request review required on `master`.
- CI passing before merge.
- Squash merge or rebase merge policy (pick one and keep it consistent).
- Force pushes disabled on protected branches.

This baseline keeps the branch model understandable for new contributors and keeps release history reliable.
