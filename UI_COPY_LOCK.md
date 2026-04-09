# UI COPY LOCK (P0)

Status: LOCKED for stabilization phase.
Date: 2026-04-09

## 1) Start / Menu

### `/start` for existing user
Text:
```
🧠 Clarity CBT
Разбор тревожной мысли за 3–7 минут по шагам КПТ.

Выбери действие:
```
Buttons:
- 🎯 Новая мысль
- 📜 История | 📊 Статистика
- ⚙️ Настройки | ❓ Помощь

Rule:
- No duplicate greeting blocks.
- Exactly one menu card.

## 2) Step headers style
Use single style everywhere:
- `<emoji> Шаг N • Название`
- one separator line
- short instruction

## 3) Intensity prompts
Text style:
- `0 · 25 · 50 · 75 · 100`
- include manual input fallback (`Введи число от 0 до 100`)

## 4) Distortion helper
For `Не уверен`:
- show inline details list
- open detailed card in same message (edit)
- actions:
  - ✅ Выбрать это искажение
  - ⬅️ Назад к выбору

## 5) Navigation standard
Inline info screens must include:
- `🏠 В меню`
Back paths where relevant:
- `⬅️ Назад`

## 6) Voice/tone
- concise
- professional
- non-judgmental
- no slang, no over-friendly fluff

## 7) Change policy
Any copy change touching locked screens requires:
1. PR note with old/new text
2. manual smoke on real Telegram client
3. owner approval before release
