# AI Shield v2 Smoke Checklist

Date: __________
Tester: __________

## Step 7 rewrite reliability
- [ ] Trigger `🤖 Помоги переформулировать` with normal input
- [ ] Receive 3 options (LLM or local fallback) without crash
- [ ] Repeated tap within few seconds does not spam requests (cooldown works)
- [ ] Generic/unrelated outputs are not shown as accepted LLM result

## Fallback behavior
- [ ] With provider error, flow still works via local options
- [ ] No dead-end after fallback

## Observability
- [ ] `/funnel` shows AI quality block
- [ ] Counters increment logically during tests

## Pass criteria
- [ ] Stable outputs and no UX break
- [ ] AI guardrails active and visible in metrics
