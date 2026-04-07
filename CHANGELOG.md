# Changelog

## 2026-04-07

### Added
- MVP Telegram bot skeleton with `/start` and polling.
- `.env` token loading and secret-safe `.gitignore`.
- SQLite schema (`users`, `settings`, `entries`) with auto-init.
- Consent gate with disclaimer before access.
- Full CBT flow:
  - thought capture
  - emotion + intensity before
  - cognitive distortion
  - evidence for/against
  - alternative thought
  - intensity after + delta
- History view for last entries.
- Tone settings (`warm` / `neutral`).
- User systemd deployment (`cbt-clarity.service`).

### Safety
- Crisis-safe detection and emergency guidance flow.
- Crisis events logged with dedicated marker.

### Product improvements (v1.1)
- Alternative-thought hint templates (inline buttons).
- Enriched result screen with personalized next-step recommendation.
- History filters (`emotion`, `distortion`, `days`).
- Daily soft reminders with `/reminders on|off`.
- Export progress via `/export txt|json`.
- 60-second onboarding (3 screens) + `/onboarding`.

### UX polish
- Cancel/menu fallback in flow (`Отмена`, `В меню`, `/cancel`).
- Consistent step headers (`Шаг X/8 • ...`).
- End-of-flow CTA and smoother menu return.
- Quick history shortcuts (`История 7д`, `История 30д`, `История тревога`).

### Data model upgrades
- Draft/completed entry model (`is_completed`, `completed_at`).
- Distortion normalization (`distortion_code` + label).
- Reminder anti-duplicate guard (`last_nudge_at`).
