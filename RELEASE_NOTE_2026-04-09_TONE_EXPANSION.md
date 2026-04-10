# Release Note — 2026-04-09 (Tone Expansion)

## Included
1. 4 tone profiles supported in settings:
   - warm
   - neutral
   - coach
   - direct
2. Tone-aware copy for core transitions and final preface.
3. Tone-aware behavior for AI components:
   - step 7 rewrite style hinting
   - AI summary style hinting
   - distortion suggestion tone hinting
4. Tone consistency applied to onboarding/help/history transitions.

## Validation
- Unit tests green (`test_callback_routes.py`, `test_flow_happy_path.py`).
- Service status: active after restart.
- Manual check via `TONE_SMOKE_CHECKLIST.md`.
