#!/bin/bash
set -e

pkill -f Xvfb || true
pkill -f chrome || true

# 2. Remove the stale lock files that cause the "Server is already active" error
rm -f /tmp/.X99-lock

rm -f "$USER_CHROME_DIR/SingletonLock"
rm -f "$USER_CHROME_DIR/SingletonSocket"
rm -f "$USER_CHROME_DIR/SingletonCookie"

export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 & sleep 2

echo "initialized" | xclip -selection clipboard

exec  python -m uvicorn src.main:app --host 0.0.0.0 --port 9831
# exec tail -f /dev/null