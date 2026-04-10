# AI Shield v2 Plan

Date: 2026-04-09
Status: in progress

## Goal
Increase AI output reliability before wider audience testing.

## Steps
- [x] Step 1: Add AI guardrails (generic-response rejection + per-user cooldown + in-process cache).
- [x] Step 2: Add fallback telemetry counters (LLM success/fallback ratio).
- [x] Step 3: Add concise admin visibility for AI quality in `/funnel` (or admin panel card).
- [x] Step 4: Smoke and release note.

## Rule
One step = one commit + tests + restart.
