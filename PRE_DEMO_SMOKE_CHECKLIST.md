# PRE-DEMO Smoke Checklist (friends group)

Run right before sharing bot publicly.

## 1) First impression
- [ ] `/start` shows clean single menu card
- [ ] Branding is `Ясно?` everywhere (no `Clarity` in visible user UX)
- [ ] Main menu text is clear and not overloaded

## 2) Core flow
- [ ] `Новая мысль` -> step 1 accepts input
- [ ] Step 2 emotion works, including `Не могу определиться`
- [ ] Step 3 quick intensity buttons work
- [ ] Step 4 distortion helper works (`Не уверен` -> details -> pick)
- [ ] Step 7 hints do NOT force skip to step 8
- [ ] Step 8 quick intensity completes and shows final card

## 3) Final card quality
- [ ] Shows: progress (before/after/delta)
- [ ] Shows: key insight + action + anchor
- [ ] Follow-up button works (`Напомнить через 3 часа`)

## 4) Stability and anti-spam
- [ ] No menu dead-ends (`В меню` always works)
- [ ] Timeout reminders are not duplicated/spammy

## 5) Admin safety
- [ ] `/admin`, `/funnel`, `/export` are owner-only
- [ ] Public users do not see admin commands in help/menu
