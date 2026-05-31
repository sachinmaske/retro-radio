#!/bin/bash
# One-time MPD setup for local testing on macOS (Homebrew).
set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
MPD_DIR="$HOME/.mpd"
CONF_SRC="$REPO_DIR/config/mpd.mac.conf"
CONF_DST="$MPD_DIR/mpd.conf"

mkdir -p "$MPD_DIR/playlists"
mkdir -p "$HOME/Music"

if [ ! -f "$CONF_DST" ]; then
  cp "$CONF_SRC" "$CONF_DST"
  echo "Created $CONF_DST"
else
  echo "Config exists: $CONF_DST"
fi

# Stop any broken service, start fresh
brew services stop mpd 2>/dev/null || true
pkill -x mpd 2>/dev/null || true
sleep 1

if mpd --kill 2>/dev/null; then
  sleep 1
fi

mpd
sleep 1

if mpc status >/dev/null 2>&1; then
  echo "MPD OK — $(mpc status | head -1)"
  echo ""
  echo "Optional: auto-start on login:"
  echo "  brew services start mpd"
  echo ""
  echo "Note: brew services needs $CONF_DST (same file mpd reads by default)."
else
  echo "MPD failed. Check log:"
  echo "  tail -20 $MPD_DIR/log"
  exit 1
fi
