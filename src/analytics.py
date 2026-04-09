import json
from typing import Any

from db import get_conn


def log_event(
    event_name: str,
    tg_user_id: int | None = None,
    session_id: str | None = None,
    step: int | None = None,
    meta: dict[str, Any] | None = None,
) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO events (event_name, tg_user_id, session_id, step, meta_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            event_name,
            tg_user_id,
            session_id,
            step,
            json.dumps(meta or {}, ensure_ascii=False),
        ),
    )
    conn.commit()
    conn.close()
