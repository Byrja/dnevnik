# NEXT ACTIONS — P0 Stabilization Pack

## Goal
Move Clarity CBT from unstable UX-beta to stable demo-ready baseline.

## Tasks
1. Create `UI_COPY_LOCK.md` (approved menu + key step texts).
2. Add regression tests for:
   - `menu:new`
   - `dist_info:*` + `dist_pick:*`
   - `int_before:*` and `int_after:*`
3. Run interaction cleanup pass (single-card where possible).
4. Update `TESTING.md` with strict release gate.
5. Run smoke on real Telegram client and mark checklist.

## Done Criteria
- No silent/dead-end transitions in main flow.
- No duplicate start/menu clutter.
- All listed callback patterns pass.
- P0 checklist all green.
