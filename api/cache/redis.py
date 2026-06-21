import json
import os
import redis

TTL = 60 * 60 * 24  # 24h

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(
            os.getenv("REDIS_URL", "redis://redis:6379/0"),
            decode_responses=True,
        )
    return _client


def get_cached(key: str) -> dict | None:
    data = get_redis().get(key)
    return json.loads(data) if data else None


def set_cache(key: str, value: dict, ttl: int = TTL) -> None:
    get_redis().setex(key, ttl, json.dumps(value))
