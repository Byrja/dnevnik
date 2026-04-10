# Clarity CBT 🧠

Telegram-бот для когнитивно-поведенческой терапии (КПТ). Помогает структурно разобрать тревожные мысли за 3-7 минут.

## Возможности

- ✅ **8-шаговый CBT-разбор**: мысль → эмоция → интенсивность → искажение → факты → альтернатива
- ✅ **Визуальный прогресс**: progress bar до/после разбора
- ✅ **Статистика**: отслеживание прогресса, стрик-трекер
- ✅ **История**: фильтрация по эмоциям, искажениям, периодам
- ✅ **Crisis-safe**: детекция кризисных сообщений + поддержка
- ✅ **Экспорт**: txt/json для анализа данных

## Команды

| Команда | Описание |
|---------|---------|
| `/start` | Начать работу |
| `/new` | Новая карточка |
| `/history` | История карточек |
| `/stats` | Твоя статистика |
| `/help` | Справка |
| `/settings` | Настройки тона |
| `/onboarding` | Повторить ознакомление |
| `/reminders on\|off` | Вкл/выкл напоминания |
| `/export txt\|json` | Экспорт данных |

## Быстрый старт

```bash
# 1. Клонируй репозиторий
git clone https://github.com/Byrja/dnevnik.git
cd dnevnik

# 2. Создай виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate

# 3. Установи зависимости
pip install -r requirements.txt

# 4. Настрой токен
cp .env.example .env
# Отредактируй .env и добавь TELEGRAM_BOT_TOKEN

# 5. Запусти
python src/main.py
```

Или используй скрипт:
```bash
./run_local.sh
```

## Структура проекта

```
dnevnik/
├── src/
│   ├── main.py      # Точка входа
│   ├── handlers.py  # Обработчики команд
│   ├── texts.py     # Тексты интерфейса
│   ├── state.py     # Состояния ConversationHandler
│   ├── db.py        # SQLite работа с БД
│   └── logger.py    # Логирование
├── data.db          # SQLite база (в .gitignore)
├── requirements.txt  # Зависимости
├── run.sh           # Production launcher
├── run_local.sh     # Local development launcher
├── .env.example     # Пример переменных окружения
├── CHANGELOG.md     # История изменений
└── TESTING.md       # Тестирование
```

## Разработка

### Тестирование
```bash
python -m py_compile src/*.py  # Проверка синтаксиса
python -m unittest tests/test_callback_routes.py
```

### Release gate (P0)
```bash
./scripts/run_release_gate_p0.sh
```
Обновляет `RELEASE_GATE_STATUS_2026-04-09.md` по результатам автопроверок.

Перед любыми UI-правками обязательно сверяться с:
- `UI_COPY_LOCK.md`

### LLM rewrite on Step 7 (optional)
By default bot uses local rewrite templates. To enable real LLM:
```bash
LLM_MODE=on
LLM_PROVIDER=openai
LLM_API_KEY=...
LLM_MODEL=gpt-4o-mini
```
If LLM is unavailable, bot automatically falls back to local options.

### Деплой (production)
```bash
# На сервере
./run.sh
```

## Лицензия

MIT
