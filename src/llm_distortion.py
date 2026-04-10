import json
import os
from typing import Optional
from urllib import request
from urllib.error import HTTPError, URLError

LABELS = [
    "Катастрофизация",
    "Чтение мыслей",
    "Черно-белое мышление",
    "Обесценивание позитивного",
    "Сверхобобщение",
    "Персонализация",
    "Эмоц. обоснование",
    "Долженствование",
    "Навешивание ярлыков",
    "Предсказание будущего",
    "Другое",
]


def _heuristic(thought: str) -> list[str]:
    t = (thought or "").lower()
    out: list[str] = []
    if any(x in t for x in ["всё", "точно", "конец", "ужас", "катастроф"]):
        out.append("Катастрофизация")
    if any(x in t for x in ["они думают", "подумают", "сочтут", "осудят"]):
        out.append("Чтение мыслей")
    if any(x in t for x in ["всегда", "никогда", "или", "провал", "идеаль"]):
        out.append("Черно-белое мышление")
    if any(x in t for x in ["должен", "обязан"]):
        out.append("Долженствование")
    if not out:
        out = ["Катастрофизация", "Предсказание будущего"]
    return out[:2]


def suggest_distortions(thought: str, emotion: str) -> list[str]:
    if os.getenv("LLM_MODE", "off").strip().lower() not in {"on", "1", "true", "yes"}:
        return _heuristic(thought)

    provider = os.getenv("LLM_PROVIDER", "openrouter").strip().lower()
    api_key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "openai/gpt-oss-20b:free").strip()
    if not api_key:
        return _heuristic(thought)

    if provider == "openrouter":
        url = "https://openrouter.ai/api/v1/chat/completions"
    elif provider == "openai":
        url = "https://api.openai.com/v1/chat/completions"
    elif provider == "groq":
        url = "https://api.groq.com/openai/v1/chat/completions"
    elif provider == "fireworks":
        url = "https://api.fireworks.ai/inference/v1/chat/completions"
    else:
        return _heuristic(thought)

    system = (
        "Ты помощник КПТ. Выбери 2 наиболее вероятных когнитивных искажения из фиксированного списка. "
        "Ответ только JSON: {\"top\":[\"...\",\"...\"]}."
    )
    user = (
        "Список: " + ", ".join(LABELS) + "\n"
        f"Мысль: {thought}\n"
        f"Эмоция: {emotion}\n"
    )

    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
        }
    ).encode("utf-8")

    req = request.Request(
        url,
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        # best effort parse
        try:
            obj = json.loads(content)
            top = obj.get("top", [])
        except Exception:
            top = []
            for label in LABELS:
                if label.lower() in content.lower():
                    top.append(label)
        cleaned = [x for x in top if x in LABELS]
        if len(cleaned) >= 2:
            return cleaned[:2]
        if len(cleaned) == 1:
            h = _heuristic(thought)
            if h[0] != cleaned[0]:
                return [cleaned[0], h[0]]
            return [cleaned[0], h[1] if len(h) > 1 else "Другое"]
        return _heuristic(thought)
    except (HTTPError, URLError, TimeoutError, KeyError, json.JSONDecodeError):
        return _heuristic(thought)
