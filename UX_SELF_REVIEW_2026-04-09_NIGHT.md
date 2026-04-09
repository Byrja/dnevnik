# UX Self-Review (Night pass) — 2026-04-09

Goal: independently review current flow and capture concrete improvements for next day.

## Overall
Current state is solid beta with strong core logic. Main opportunities are in polish, compression of message noise, and clearer user momentum between steps.

---

## Step-by-step findings

### Start / Main menu
What is good:
- One clean card, stronger brand, admin hidden for regular users.

What can be better:
1. Add one compact progress line for returning users: `Последний сдвиг: ΔX` (if available).
2. Add context shortcut in menu card: `Если накал >70 — начни с “Новая мысль”`.

Priority: P1

---

### Step 1 (thought)
What is good:
- Strong prompt examples, A/B test enabled.

What can be better:
1. Add one negative example with clearer contrast (`слишком общее` vs `рабочее`).
2. If vague text repeats 2 times, auto-offer one guided template button.

Priority: P1

---

### Step 2 (emotion)
What is good:
- `Не могу определиться` helper now useful and has back path.

What can be better:
1. Add quick multi-select option (`основная + вторичная`) for richer history analytics.
2. Save emotion-choice path source (`direct` vs `helper`) in events.

Priority: P2

---

### Step 3 / 8 (intensity)
What is good:
- Quick buttons + manual fallback works.

What can be better:
1. Add inline confirmation line after quick tap (`Принято: 60/100`) to reduce uncertainty.
2. Add guard for accidental double-tap (idempotent callback handling).

Priority: P1

---

### Step 4 (distortion)
What is good:
- Detailed cards, pick-from-detail, back flow.

What can be better:
1. Add `Похоже на...` heuristic from text to suggest top-2 distortions (non-blocking hint).
2. Add short “how to counter” sentence directly after distortion pick.

Priority: P1/P2

---

### Step 5/6 (facts)
What is good:
- Strong anti-vague prompts.

What can be better:
1. Add micro-formatter hint: `• факт 1\n• факт 2` for better readability.
2. If user gives one long sentence, suggest splitting to 2 bullets.

Priority: P1

---

### Step 7 (alternative thought)
What is good:
- Rich hint set + AI helper + no forced jump to step 8.

What can be better:
1. Add one-click `Использовать вариант 1/2/3` buttons (fills draft and asks to edit).
2. Add quality-check after user sends alternative thought (`реалистично? / поддерживает действие?`).

Priority: P1

---

### Final card
What is good:
- Insight + action + anchor + follow-up.

What can be better:
1. Add optional `Сохранить якорь` quick action to history metadata.
2. Add `Повторить через 24ч` follow-up option beside 3h.

Priority: P1

---

### History screen
What is good:
- Useful summary (avg delta + top emotion/distortion).

What can be better:
1. Add `7д / 30д` inline filter buttons (not text command only).
2. Add compact trend line by day (ASCII mini chart).

Priority: P1

---

## Cross-cutting technical UX items
1. Ensure all callback screens use consistent back/home buttons.
2. Add anti-spam rule: avoid sending >2 consecutive bot messages where one edited card can do.
3. Extend flow tests with explicit back-navigation checks for admin and emotion helper.

Priority: P0.5/P1

---

## Proposed next-day implementation order
1. P1-A: Step 7 one-click use of AI options (+ tests)
2. P1-B: Intensity quick-tap confirmation + idempotency
3. P1-C: History inline filters (7d/30d)
4. P1-D: Final card extra follow-up option (24h)

---

## Acceptance checkpoint for "show to friends"
- No dead-end paths.
- No obvious message clutter.
- First run explains value in <15 seconds.
- Final card gives clear insight and action.
- History feels useful (not raw dump).
