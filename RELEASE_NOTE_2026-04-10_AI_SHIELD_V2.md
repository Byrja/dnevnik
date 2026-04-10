# Release Note — 2026-04-10 (AI Shield v2)

## Included
1. Step 7 AI rewrite hardening:
   - per-user cooldown
   - in-process cache (TTL)
   - generic-response rejection
2. Telemetry counters for AI rewrite quality:
   - requests, llm_success, cache_hit, provider_fail, generic_reject
3. Admin visibility:
   - AI quality block in `/funnel`

## Operational behavior
- If provider fails or output quality is poor, bot automatically falls back to local rewrite options.
- Core flow remains available without AI.

## Validation
- tests: callback routes + flow tests green
- service active after restart
- smoke checklist: `AI_SHIELD_SMOKE_CHECKLIST.md`
