import os
import re
import time
from typing import Optional

import json
from urllib import request
from urllib.error import URLError, HTTPError


def llm_enabled() -> bool:
    return os.getenv("LLM_MODE", "off").strip().lower() in {"on", "1", "true", "yes"}


_CACHE: dict[str, tuple[float, list[str]]] = {}
_CACHE_TTL_SEC = 6 * 60 * 60


def _keywords(text: str) -> set[str]:
    words = re.findall(r"[а-яА-Яa-zA-Z0-9]{4,}", (text or "").lower())
    stop = {"когда", "если", "потому", "который", "которые", "очень", "просто", "сейчас", "можно", "будет", "снова", "себя", "своей", "этого", "этой", "такой", "there", "with", "that", "this", "from"}
    return {w for w in words if w not in stop}


def _is_contextual(options: list[str], thought: str, evidence_against: str) -> bool:
    ctx = _keywords(thought) | _keywords(evidence_against)
    if not ctx:
        return True
    joined = " ".join(options).lower()
    hit = sum(1 for w in ctx if w in joined)
    return hit >= 1


def _looks_generic(options: list[str]) -> bool:
    joined = " ".join(options).lower()
    generic_markers = [
        "я не идеален",
        "я могу работать над собой",
        "я могу ошибаться",
        "стать лучше",
        "всё будет хорошо",
    ]
    # If most text is generic and lacks concrete context words, reject.
    return sum(1 for m in generic_markers if m in joined) >= 2


def _chat_rewrite_options(thought: str, evidence_against: str, *, api_key: str, model: str, url: str) -> Optional[list[str]]:
    if not api_key:
        return None

    model = model.strip()
    system = (
        "Ты — помощник КПТ. Задача: дать 3 качественные альтернативные мысли на русском. "
        "Стиль: спокойный, реалистичный, без магического мышления и без категоричности. "
        "Обязательно опирайся на факты против автоматической мысли и на контекст пользователя. "
        "Нельзя писать общие универсальные фразы, не связанные с исходной мыслью. "
        "Каждый вариант должен явно быть про ту же ситуацию. "
        "Формат строго: 1) ... 2) ... 3) ... (каждая строка отдельно). "
        "Ограничения: до 180 символов на вариант, без медицинских советов, без оценочных ярлыков. "
        "Варианты по типу: (1) мягкий, (2) рациональный, (3) поддерживающий-действующий."
    )
    user = (
        f"Исходная мысль: {thought}\n"
        f"Факты против: {evidence_against or 'нет явных фактов'}\n"
        "Сформулируй 3 альтернативные мысли от первого лица."
    )

    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.35,
        }
    ).encode("utf-8")

    req = request.Request(
        url,
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError):
        return None
    content = data["choices"][0]["message"]["content"]

    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
    out: list[str] = []
    for ln in lines:
        if ln[0].isdigit() and ")" in ln:
            out.append(ln.split(")", 1)[1].strip())
        elif ln.startswith(("-", "•")):
            out.append(ln[1:].strip())
        else:
            out.append(ln)
        if len(out) == 3:
            break

    if len(out) < 3:
        return None

    out = out[:3]
    if not _is_contextual(out, thought, evidence_against):
        return None
    return out


def _openai_rewrite_options(thought: str, evidence_against: str) -> Optional[list[str]]:
    api_key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()
    return _chat_rewrite_options(
        thought=thought,
        evidence_against=evidence_against,
        api_key=api_key,
        model=model,
        url="https://api.openai.com/v1/chat/completions",
    )


def _groq_rewrite_options(thought: str, evidence_against: str) -> Optional[list[str]]:
    api_key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile").strip()
    return _chat_rewrite_options(
        thought=thought,
        evidence_against=evidence_against,
        api_key=api_key,
        model=model,
        url="https://api.groq.com/openai/v1/chat/completions",
    )


def _fireworks_rewrite_options(thought: str, evidence_against: str) -> Optional[list[str]]:
    api_key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "accounts/fireworks/models/llama-v3p1-8b-instruct").strip()
    return _chat_rewrite_options(
        thought=thought,
        evidence_against=evidence_against,
        api_key=api_key,
        model=model,
        url="https://api.fireworks.ai/inference/v1/chat/completions",
    )


def _openrouter_rewrite_options(thought: str, evidence_against: str) -> Optional[list[str]]:
    api_key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "openai/gpt-4o-mini").strip()
    return _chat_rewrite_options(
        thought=thought,
        evidence_against=evidence_against,
        api_key=api_key,
        model=model,
        url="https://openrouter.ai/api/v1/chat/completions",
    )


def rewrite_options(thought: str, evidence_against: str, tone: str = "warm") -> Optional[list[str]]:
    if not llm_enabled():
        return None

    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()

    # Tone-aware style hints through lightweight pre-processing.
    t_thought = thought
    if tone == "direct":
        t_thought = f"(стиль: прямой) {thought}"
    elif tone == "coach":
        t_thought = f"(стиль: коуч) {thought}"
    elif tone == "neutral":
        t_thought = f"(стиль: нейтральный) {thought}"

    cache_key = f"{provider}|{tone}|{thought.strip()}|{evidence_against.strip()}"
    now = time.time()
    cached = _CACHE.get(cache_key)
    if cached and now - cached[0] <= _CACHE_TTL_SEC:
        return cached[1]

    out: Optional[list[str]] = None
    if provider == "openai":
        out = _openai_rewrite_options(thought=t_thought, evidence_against=evidence_against)
    elif provider == "groq":
        out = _groq_rewrite_options(thought=t_thought, evidence_against=evidence_against)
    elif provider == "fireworks":
        out = _fireworks_rewrite_options(thought=t_thought, evidence_against=evidence_against)
    elif provider == "openrouter":
        out = _openrouter_rewrite_options(thought=t_thought, evidence_against=evidence_against)

    if not out:
        return None
    if _looks_generic(out):
        return None

    _CACHE[cache_key] = (now, out)
    return out
