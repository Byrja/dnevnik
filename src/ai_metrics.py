from db import get_conn

_ALLOWED = {"requests", "cache_hit", "llm_success", "provider_fail", "generic_reject"}


def inc_metric(key: str, delta: int = 1) -> None:
    if key not in _ALLOWED or delta <= 0:
        return
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO ai_metrics (metric_key, metric_value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(metric_key)
        DO UPDATE SET metric_value = metric_value + excluded.metric_value,
                      updated_at = CURRENT_TIMESTAMP
        """,
        (key, delta),
    )
    conn.commit()
    conn.close()


def get_metrics() -> dict[str, int]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT metric_key, metric_value FROM ai_metrics")
    rows = cur.fetchall()
    conn.close()
    out = {k: 0 for k in _ALLOWED}
    for r in rows:
        out[r[0]] = int(r[1])
    return out
