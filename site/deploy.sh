#!/usr/bin/env bash
# Pull the tracked branch and republish the site, but only if it builds.
#
# The point of this script is the thing it refuses to do. A push that breaks
# the build must leave the currently published site exactly where it is: the
# new pages are built into a staging directory and only swapped in once the
# build has succeeded AND every link in it resolves. A deploy that can take the
# site down on a bad commit is worse than no deploy, because it fails at the
# moment somebody is iterating and least wants to debug infrastructure.
#
# Run by j2s-deploy.timer every two minutes. Does nothing at all when the
# remote has not moved, so the usual cost is one git fetch.
set -uo pipefail

REPO="$HOME/ventures/j2s-site"
BRANCH="${J2S_BRANCH:-site/concept-first}"
PY="$HOME/.local/bin/python3.12"
STATE="$HOME/.local/state/soulful/j2s-deploy"
mkdir -p "$STATE"

cd "$REPO" || exit 1
log() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*"; }

# Never clobber uncommitted work. If the worktree is dirty something is going
# on that a cron job should not resolve by itself.
if [ -n "$(git status --porcelain)" ]; then
  log "worktree dirty, refusing to deploy"
  exit 0
fi

git fetch -q origin "$BRANCH" || { log "fetch failed"; exit 1; }
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse "origin/$BRANCH")
[ "$LOCAL" = "$REMOTE" ] && exit 0

log "deploying $BRANCH ${LOCAL:0:8} -> ${REMOTE:0:8}"
git checkout -q -B "$BRANCH" "origin/$BRANCH" || { log "checkout failed"; exit 1; }

STAGE="$REPO/site/out.stage"
rm -rf "$STAGE"

notify_fail() {
  # Tell him once per commit, not once per poll: a job that texts every two
  # minutes about the same failure is a job he will mute.
  if [ "$(cat "$STATE/last-notified" 2>/dev/null)" != "$REMOTE" ]; then
    echo "$REMOTE" > "$STATE/last-notified"
    "$HOME/soulful/box/talk/tg.py" "Deploy of ${REMOTE:0:8} failed at the $1 step, so the live site is still on the previous commit. Log: journalctl --user -u j2s-deploy -n 40" >/dev/null 2>&1 || true
  fi
}

if ! SITE_OUT="$STAGE" "$PY" site/build.py; then
  log "BUILD FAILED, keeping the published site"
  notify_fail "build"; rm -rf "$STAGE"; exit 1
fi

if ! SITE_OUT="$STAGE" "$PY" site/check.py; then
  log "LINK CHECK FAILED, keeping the published site"
  notify_fail "link check"; rm -rf "$STAGE"; exit 1
fi

# Swap. The server resolves site/out by path on every request, so the window
# where it does not exist is the time taken by two renames.
rm -rf "$REPO/site/out.old"
[ -d "$REPO/site/out" ] && mv "$REPO/site/out" "$REPO/site/out.old"
mv "$STAGE" "$REPO/site/out"
rm -rf "$REPO/site/out.old"

echo "$REMOTE" > "$STATE/last-deployed"
log "published ${REMOTE:0:8}"
