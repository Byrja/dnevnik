# RELEASE GATE STATUS — 2026-04-09

## Automated checks
- [x] `python -m py_compile src/*.py` passes
- [x] `python -m unittest tests/test_callback_routes.py` passes (5 tests)

## Manual smoke checks
- [ ] `/start` single menu card
- [ ] `menu:new` -> next text processed
- [ ] Step 3 quick buttons
- [ ] Step 8 quick buttons
- [ ] `Не уверен -> details -> pick` end-to-end

## UX/safety checks
- [ ] No extra chat spam in inline flow
- [ ] Menu matches `UI_COPY_LOCK.md`
- [ ] Crisis-safe branch still valid

## Decision
Current gate: **NO-GO (manual smoke pending)**
