#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

STATUS_FILE="$ROOT/RELEASE_GATE_STATUS_2026-04-09.md"
TS="$(date -u +"%Y-%m-%d %H:%M:%S UTC")"

PY_COMPILE_OK="no"
UNIT_OK="no"

if python3 -m py_compile src/*.py >/dev/null 2>&1; then
  PY_COMPILE_OK="yes"
fi

if python3 -m unittest tests/test_callback_routes.py >/dev/null 2>&1; then
  UNIT_OK="yes"
fi

cat > "$STATUS_FILE" <<EOF
# RELEASE GATE STATUS — 2026-04-09

Updated: $TS

## Automated checks
- [$( [ "$PY_COMPILE_OK" = "yes" ] && echo x || echo " " )] \`python -m py_compile src/*.py\`
- [$( [ "$UNIT_OK" = "yes" ] && echo x || echo " " )] \`python -m unittest tests/test_callback_routes.py\`

## Manual smoke checks
- [ ] /start single menu card
- [ ] menu:new -> next text processed
- [ ] Step 3 quick buttons
- [ ] Step 8 quick buttons
- [ ] Не уверен -> details -> pick end-to-end

## UX/safety checks
- [ ] No extra chat spam in inline flow
- [ ] Menu matches UI_COPY_LOCK.md
- [ ] Crisis-safe branch still valid

## Decision
Current gate: **NO-GO (manual smoke pending)**
EOF

echo "Gate status updated: $STATUS_FILE"
