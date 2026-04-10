import os
from typing import Optional

import json
from urllib import request
from urllib.error import URLError, HTTPError


def llm_enabled() -> bool:
    return os.getenv("LLM_MODE", "off").strip().lower() in {"on", "1", "true", "yes"}


def _openai_rewrite_options(thought: str, evidence_against: str) -> Optional[list[str]]:
    api_key = os.getenv("LLM_API_KEY", "").strip()
    if not api_key:
        return None

    model = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()
    system = (
        "Ты помогаешь переформулировать мысль в рамках КПТ. "
        "Верни строго 3 коротких варианта на русском языке: мягкий, рациональный, поддерживающий. "
        "Каждый вариант до 220 символов. Без медицинских советов."
    )
    user = (
        f"Исходная мысль: {thought}\n"
        f"Факты против: {evidence_against}\n"
        "Формат ответа строго:\n"
        "1) ...\n2) ...\n3) ..."
    )

    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.5,
        }
    ).encode("utf-8")

    req = request.Request(
        "https://api.openai.com/v1/chat/completions",
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


def rewrite_options(thought: str, evidence_against: str) -> Optional[list[str]]:
    if not llm_enabled():
        return None

    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    if provider == "openai":
        return _openai_rewrite_options(thought=thought, evidence_against=evidence_against)
    return None
