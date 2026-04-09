# Analytics Event Map (P2.2)

Goal: track funnel conversion and drop-off by step.

## Event schema (planned)
- `event_name` (text)
- `tg_user_id` (int)
- `session_id` (text, nullable)
- `step` (int, nullable)
- `meta_json` (text/json, nullable)
- `created_at` (timestamp)

## Core events
1. `menu_opened`
   - when: `/start` existing user sees menu
2. `session_started`
   - when: user enters new thought flow
3. `step_entered`
   - when: bot asks for step input (1..8)
4. `step_completed`
   - when: user provides valid input for step
5. `session_completed`
   - when: final intensity saved and entry marked completed
6. `session_aborted`
   - when: flow canceled or draft lost
7. `followup_scheduled`
   - when: user taps follow-up shortcut

## Funnel report (target)
- users/session_started
- step completion counts (1..8)
- completion rate (`session_completed / session_started`)
- major drop-off step (max loss)

## Notes
- Keep instrumentation lightweight (SQLite only).
- No personal sensitive free text in event payload by default.
