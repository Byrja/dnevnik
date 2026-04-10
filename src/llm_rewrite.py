import os
from typing import Optional

import json
from urllib import request
from urllib.error import URLError, HTTPError


def llm_enabled() -> bool:
    return os.getenv("LLM_MODE", "off").strip().lower() in {"on", "1", "true", "yes"}


def _chat_rewrite_options(thought: str, evidence_against: str, *, api_key: str, model: str, url: str) -> Optional[list[str]]:
    if not api_key:
        return None

    model = model.strip()
    system = (
        "Ты — помощник КПТ. Задача: дать 3 качественные альтернативные мысли на русском. "
        "Стиль: спокойный, реалистичный, без магического мышления и без категоричности. "
        "Обязательно опирайся на факты против автоматической мысли. "
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
    return out[:3]


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


def rewrite_options(thought: str, evidence_against: str) -> Optional[list[str]]:
    if not llm_enabled():
        return None

    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    if provider == "openai":
        return _openai_rewrite_options(thought=thought, evidence_against=evidence_against)
    if provider == "groq":
        return _groq_rewrite_options(thought=thought, evidence_against=evidence_against)
    if provider == "fireworks":
        return _fireworks_rewrite_options(thought=thought, evidence_against=evidence_against)
    if provider == "openrouter":
        return _openrouter_rewrite_options(thought=thought, evidence_against=evidence_against)
    return None
