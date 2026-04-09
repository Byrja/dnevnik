# Smoke Checklist P0 (2–3 min)

Date: __________
Tester: __________

## 1) Start/Menu
- [ ] `/start` shows exactly one menu card (no duplicate greeting blocks)
- [ ] Menu buttons visible: New / History / Stats / Settings / Help

## 2) Core callback flow
- [ ] `menu:new` starts Step 1
- [ ] After first text input, bot moves to Step 2 (no silence)

## 3) Intensity quick input
- [ ] Step 3 quick button (e.g., 60) works
- [ ] Step 8 quick button (e.g., 40) works

## 4) Distortion helper
- [ ] `Не уверен` opens detailed helper
- [ ] `Подробнее` opens description in-place
- [ ] `✅ Выбрать это искажение` moves to Step 5

## 5) Safety/basic UX
- [ ] Crisis keyword triggers support message
- [ ] No obvious message spam in inline helper flow

## Result
- [ ] PASS
- [ ] FAIL (rollback / fix required)
