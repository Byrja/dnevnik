#!/usr/bin/env bash
set -euo pipefail
cd /srv/openclaw-bus/cbt-clarity
source .venv/bin/activate
exec python src/main.py
