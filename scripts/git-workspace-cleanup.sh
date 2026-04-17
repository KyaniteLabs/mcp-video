#!/usr/bin/env bash
set -euo pipefail

# Cleanup helper for local Git workspace state.
# Safe by default: prunes stale metadata and reports candidate cleanup actions.

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not inside a Git repository." >&2
  exit 2
fi

echo "[1/5] Pruning stale worktree metadata..."
git worktree prune

echo "[2/5] Listing active worktrees..."
git worktree list

if git remote | grep -q .; then
  echo "[3/5] Fetch + prune remotes..."
  while IFS= read -r remote; do
    git fetch --prune "$remote"
    git remote prune "$remote"
  done < <(git remote)
else
  echo "[3/5] No remotes configured. Skipping remote prune."
fi

echo "[4/5] Branches tracking deleted remotes..."
git branch -vv | awk '/: gone]/{print $1}' || true

echo "[5/5] Branches already merged into current HEAD (safe delete candidates):"
git branch --merged | sed 's/^..//' | grep -v "^$(git rev-parse --abbrev-ref HEAD)$" || true

echo "Cleanup complete."
