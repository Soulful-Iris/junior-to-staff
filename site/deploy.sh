#!/usr/bin/env bash
# Build main in staging, then publish it. Keep the prior release if the build fails.
set -euo pipefail
REPO="${J2S_REPO:-$HOME/ventures/j2s-site}"
BRANCH="main"
PY="${J2S_PYTHON:-$HOME/.local/bin/python3.12}"
STATE="${J2S_DEPLOY_STATE:-$HOME/.local/state/soulful/j2s-deploy}"
mkdir -p "$STATE"
exec 9>"$STATE/deploy.lock"
flock -n 9 || exit 0
cd "$REPO"
log() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*"; }
git fetch -q origin "$BRANCH"
REMOTE=$(git rev-parse "origin/$BRANCH")
if [ "$(git rev-parse HEAD)" = "$REMOTE" ] && [ "$(cat "$STATE/last-deployed" 2>/dev/null || true)" = "$REMOTE" ]; then
  exit 0
fi
# Preserve server-local edits instead of letting them stop publication of main.
if [ -n "$(git status --porcelain)" ]; then
  log "saving server-local changes in git stash before publishing main"
  git stash push --include-untracked -m "server-local changes before publishing $REMOTE"
fi
git checkout -q --detach "$REMOTE"
STAGE=$(mktemp -d "$REPO/site/out.stage.XXXXXXXX")
trap 'rm -rf -- "$STAGE"' EXIT
fail() {
  log "$1 FAILED; no new successful publication recorded"
  exit 1
}
VENV="$STATE/reader-venv"
if [ ! -x "$VENV/bin/python" ]; then
  "$PY" -m venv "$VENV" || fail "VENV"
fi
REQ_HASH=$(sha256sum site/requirements.lock | cut -d' ' -f1)
if [ "$(cat "$STATE/requirements-hash" 2>/dev/null || true)" != "$REQ_HASH" ]; then
  "$VENV/bin/python" -m pip install --require-hashes -r site/requirements.lock || fail "PYTHON DEPENDENCIES"
  printf '%s\n' "$REQ_HASH" > "$STATE/requirements-hash"
fi
PY="$VENV/bin/python"
# Include the complete dependency graph, not just top-level versions.
NODE_HASH=$(sha256sum site/tools/package-lock.json | cut -d' ' -f1)
if [ ! -d site/tools/node_modules ] || [ "$(cat "$STATE/node-hash" 2>/dev/null || true)" != "$NODE_HASH" ]; then
  npm ci --prefix site/tools --ignore-scripts --no-audit --no-fund || fail "NODE DEPENDENCIES"
  printf '%s\n' "$NODE_HASH" > "$STATE/node-hash"
fi
SITE_OUT="$STAGE" "$PY" site/build.py || fail "BUILD"
# Complete prior releases remain available. Existing directory layouts are
# adopted automatically by publish.py; no manual migration is required.
"$PY" site/publish.py "$STAGE" "$REPO/site/out" "$REMOTE" "$STATE/last-deployed" || fail "PUBLICATION"
log "published ${REMOTE:0:8}"
