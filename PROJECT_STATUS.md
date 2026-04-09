# Clarity CBT — Project Status

Updated: 2026-04-09
Owner: Sasha

## Overall status
- Stage: **Stable beta / demo-ready**
- Gate: **P0 = GO**
- Current quality estimate: **~8/10**

## Completed

### P0 Stabilization ✅
- UI baseline lock: `UI_COPY_LOCK.md`
- Release gate docs: `RELEASE_GATE_P0.md`, `RELEASE_GATE_STATUS_2026-04-09.md`
- Gate automation: `scripts/run_release_gate_p0.sh`
- Manual smoke checklist: `scripts/smoke_checklist_p0.md`
- Callback route regression tests: `tests/test_callback_routes.py`
- Testing guide updated: `TESTING.md`

### Product / UX improvements ✅
- Fixed `menu:new` state entry (no silent flow)
- Quick intensity buttons on steps 3 & 8 (with manual fallback)
- Distortion helper (`Не уверен` -> details -> pick)
- Inline “pick this distortion” + back navigation
- Reduced inline chat spam (edit-in-place where suitable)
- Final result card improved (clear summary + action)
- Added daily anchor phrase in final card
- Added follow-up reminder shortcut (`+3h`) with CTA to start new thought

### P1.5 Polish ✅
- Unified visual separators/copy style
- Removed dead/legacy menu code and unused constants

## Current risks
- No deep end-to-end integration tests (only route-level regressions + manual smoke)
- LLM rewrite is currently local-template based (not real model inference)

## Next roadmap (P2)
1. Feature flag for real LLM rewrite on step 7 (safe fallback required)
2. Better analytics (step drop-off, conversion from start to completed card)
3. A/B tests for menu copy and first-step prompt
4. Expand automated tests from route checks to flow-level scenario checks

## Recommended immediate next task
- Build minimal flow-level test harness for 1 happy path + 2 critical edge paths.
