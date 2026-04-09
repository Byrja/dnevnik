# RELEASE GATE P0 (must pass before production)

Project: Clarity CBT
Gate level: P0 stabilization

## A) Build / static checks
- [ ] `python -m py_compile src/*.py` passes
- [ ] `python -m unittest tests/test_callback_routes.py` passes

## B) Core flow checks (manual)
- [ ] `/start` shows one clean menu card (no duplicate greeting blocks)
- [ ] `menu:new` starts flow and next text is processed (no silent state)
- [ ] Step 3 quick buttons (`20/40/60/80/100`) work
- [ ] Step 8 quick buttons (`20/40/60/80/100`) work
- [ ] Distortion helper: `Не уверен -> details -> pick` works end-to-end

## C) UX cleanliness checks
- [ ] No excessive chat spam on inline interactions where edit-in-place is expected
- [ ] Menu text and buttons match `UI_COPY_LOCK.md`
- [ ] Navigation buttons (`⬅️`, `🏠`) behave consistently where present

## D) Safety checks
- [ ] Crisis-safe message still triggers on crisis markers
- [ ] No dead-end states in happy path

## E) Release decision
- [ ] GO approved
- [ ] Rollback commit noted

## Rollback note
If gate fails after deploy, rollback to previous known-good commit and restart service.
