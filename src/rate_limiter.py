import os
from upstash_redis import Redis

RATE_LIMIT = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "5"))

_redis_client = None


def _get_redis() -> Redis:
    """Singleton del cliente Redis (reutiliza la conexión entre invocaciones calientes)."""
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis(
            url=os.environ.get("UPSTASH_REDIS_REST_URL", ""),
            token=os.environ.get("UPSTASH_REDIS_REST_TOKEN", ""),
        )
    return _redis_client


def check_rate_limit(chat_id: str) -> tuple[bool, int]:
    """
    Verifica si el usuario está dentro del límite de mensajes por minuto.
    Retorna (permitido, cantidad_actual).
    Si Redis falla, permite el request (fail open) para no bloquear a usuarios legítimos.
    """
    try:
        redis = _get_redis()
        key = f"rl:{chat_id}"

        count = redis.incr(key)

        # Solo seteamos el expire en el primer mensaje del minuto
        if count == 1:
            redis.expire(key, 60)

        return count <= RATE_LIMIT, count

    except Exception as e:
        print(f"[RATE_LIMIT ERROR] {e} — permitiendo request por fail-open")
        return True, 0
