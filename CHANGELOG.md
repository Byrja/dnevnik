# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] — Planned Improvements

### 🔴 High Priority
- [x] Inline buttons instead of Reply keyboard (modern UI)
- [ ] Session timeouts (remind inactive users)
- [ ] Input validation with examples ("e.g.: 75")

### 🟡 Medium Priority
- [ ] Streak tracker — gamification ("🔥 5 days streak!")
- [ ] Distortion descriptions — brief explanation on selection
- [ ] Custom emotions — user can add their own
- [ ] Undo action — `/undo` to revert last step

### 🟢 Nice to Have
- [ ] Localization — English support (i18n)
- [ ] Dark theme — Telegram Dark Mode adapter
- [ ] Webhook instead of polling — production deployment
- [ ] Health check endpoint — `/health` for monitoring

---

## [1.4.0] — 2026-04-08

### Added
- **`/help` command** — Full command reference
- **`/stats` command** — User statistics (total cards, weekly/monthly, avg delta, streak, top emotions)
- **Inline keyboard function** — `_main_menu_inline()` for future modern UI
- **New emojis** — STAR, FIRE, HELP for visual hierarchy
- **CHANGELOG.md** — Change tracking file

### Changed
- `src/texts.py` — Added HELP_RU, STATS_RU, STATS_EMPTY_RU constants
- `src/handlers.py` — Added show_help() and show_stats() functions
- `src/main.py` — Registered new command handlers
- README.md — Complete redesign with features table, structure, and commands

### Fixed
- `.gitignore` — Added .env.example to prevent env file commits

---

## [1.3.0] — 2026-04-08

### Added
- **UX/UI Improvements**
  - Emoji icons for visual hierarchy (📋, 📜, ⚙️, etc.)
  - Visual progress bars for results (█░)
  - Formatted step indicators (━━━━━━━━━━━━━━━━━━━)
  - New `_format_result()` function with visual elements
  - Improved history display with improvement indicators (↓Δ)

### Changed
- `src/texts.py` — Complete redesign with UX improvements
- `src/handlers.py` — Integrated new formatting for results and history

---

## [1.2.0] — 2026-04-08

### Added
- **Logging Module** (`src/logger.py`)
  - Structured logging with timestamps
  - Error logging with context
  - Update tracking

### Changed
- `src/handlers.py` — Added exception logging in `send_daily_nudges`
- `.env.example` — Improved documentation
- `run_local.sh` — New local development script (production path removed)

### Fixed
- `.gitignore` — Added `*.db`, `data.db`, `.env.example` to prevent DB commits

---

## [1.1.0] — Initial MVP Features

### Added
- Crisis-safe flow (detection + support message)
- Soft reminders (daily nudges scheduler)
- Smart result screen (Δ + next step recommendation)
- History with filters (emotion/distortion/period)
- Alternative thought templates (friend/facts/balanced)
- Export progress (`/export txt|json`)
- Onboarding (3 screens + how-to)
- Tone settings (warm/neutral)
- Consent flow for new users