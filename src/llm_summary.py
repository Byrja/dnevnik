import json
import os
from typing import Optional
from urllib import request
from urllib.error import HTTPError, URLError


def _provider_url(provider: str) -> Optional[str]:
    p = (provider or "").lower().strip()
    if p == "openrouter":
        return "https://openrouter.ai/api/v1/chat/completions"
    if p == "openai":
        return "https://api.openai.com/v1/chat/completions"
    if p == "groq":
        return "https://api.groq.com/openai/v1/chat/completions"
    if p == "fireworks":
        return "https://api.fireworks.ai/inference/v1/chat/completions"
    return None


def summarize_card(
    thought: str,
    emotion: str,
    distortion: str,
    before: int | None,
    after: int | None,
    alt: str,
    tone: str = "warm",
) -> Optional[str]:
    if os.getenv("LLM_MODE", "off").strip().lower() not in {"on", "1", "true", "yes"}:
        return None

    api_key = os.getenv("LLM_API_KEY", "").strip()
    provider = os.getenv("LLM_PROVIDER", "openrouter").strip().lower()
    model = os.getenv("LLM_MODEL", "openai/gpt-oss-20b:free").strip()
    url = _provider_url(provider)
    if not api_key or not url:
        return None

    delta = None
    if isinstance(before, int) and isinstance(after, int):
        delta = before - after

    style_hint = {
        "warm": "Стиль: мягкий, поддерживающий.",
        "neutral": "Стиль: нейтральный, деловой.",
        "coach": "Стиль: коучинговый, мотивирующий к действию.",
        "direct": "Стиль: прямой, короткий, без лишних слов.",
    }.get((tone or "warm").lower(), "Стиль: нейтральный.")

    system = (
        "Ты помощник КПТ. Сделай краткое резюме одной карточки. "
        "Формат строго 4 строки на русском: "
        "1) Главный триггер/контекст, "
        "2) Ключевое искажение простыми словами, "
        "3) Сдвиг по интенсивности, "
        "4) Следующий шаг на сегодня. "
        "Без медицинских рекомендаций, без воды, до 420 символов суммарно. "
        + style_hint
    )
    user = (
        f"Мысль: {thought}\n"
        f"Эмоция: {emotion}\n"
        f"Искажение: {distortion}\n"
        f"До: {before}\n"
        f"После: {after}\n"
        f"Delta: {delta}\n"
        f"Альтернативная мысль: {alt}\n"
    )

    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.25,
        }
    ).encode("utf-8")

    req = request.Request(
        url,
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=18) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        if len(content) < 40:
            return None
        if len(content) > 900:
            content = content[:900]
        return content
    except (HTTPError, URLError, TimeoutError, KeyError, json.JSONDecodeError):
        return None
