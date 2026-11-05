#!/bin/bash
set -e

export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 & sleep 2
exec  python -m uvicorn src.main:app --host 0.0.0.0 --port 9831