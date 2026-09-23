#!/usr/bin/env bash
# Build off-line, verify, then switch one release pointer. Never delete live on failure.
set -euo pipefail
REPO="${J2S_REPO:-$HOME/ventures/j2s-site}"
BRANCH="${J2S_BRANCH:-main}"
PY="${J2S_PYTHON:-$HOME/.local/bin/python3.12}"
STATE="${J2S_DEPLOY_STATE:-$HOME/.local/state/soulful/j2s-deploy}"
mkdir -p "$STATE"
exec 9>"$STATE/deploy.lock"
flock -n 9 || exit 0
cd "$REPO"
log() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*"; }
if [ -n "$(git status --porcelain)" ]; then
  log "worktree dirty, refusing to deploy"
  exit 0
fi
git fetch -q origin "$BRANCH"
REMOTE=$(git rev-parse "origin/$BRANCH")
if [ "$(git rev-parse HEAD)" = "$REMOTE" ] && [ "$(cat "$STATE/last-deployed" 2>/dev/null || true)" = "$REMOTE" ]; then
  exit 0
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
REQ_HASH=$(sha256sum site/requirements.txt | cut -d' ' -f1)
if [ "$(cat "$STATE/requirements-hash" 2>/dev/null || true)" != "$REQ_HASH" ]; then
  "$VENV/bin/python" -m pip install -r site/requirements.txt || fail "PYTHON DEPENDENCIES"
  printf '%s\n' "$REQ_HASH" > "$STATE/requirements-hash"
fi
PY="$VENV/bin/python"
# A reviewed transitive lock is still required to close audit SITE-05.
# Keep the existing install policy here until that artifact is supplied.
NODE_HASH=$(sha256sum site/tools/package.json | cut -d' ' -f1)
if [ ! -d site/tools/node_modules ] || [ "$(cat "$STATE/node-hash" 2>/dev/null || true)" != "$NODE_HASH" ]; then
  npm install --prefix site/tools --ignore-scripts --package-lock=false --no-audit --no-fund || fail "NODE DEPENDENCIES"
  printf '%s\n' "$NODE_HASH" > "$STATE/node-hash"
fi
SITE_OUT="$STAGE" "$PY" site/build.py || fail "BUILD"
SITE_OUT="$STAGE" "$PY" site/check.py || fail "LINK CHECK"
SITE_OUT="$STAGE" "$PY" site/check_reading.py || fail "READING CHECK"
# Complete prior releases remain available. Legacy directory layouts require an
# explicit one-time migration; see PUBLISHING.md. Never auto-delete the live tree.
"$PY" site/publish.py "$STAGE" "$REPO/site/out" "$REMOTE" "$STATE/last-deployed" || fail "PUBLICATION"
log "published ${REMOTE:0:8}"
