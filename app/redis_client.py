import os

import redis
from dotenv import load_dotenv


load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
FAILURE_WINDOW_SECONDS = 300

redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True,
)


def failure_key(monitor_id: int) -> str:
    return f"monitor:{monitor_id}:failures"


def register_failure(monitor_id: int) -> int | None:
    """Increment and return a monitor's failure count for the active window. """
    try:
        key = failure_key(monitor_id)
        count = redis_client.incr(key)

        if count == 1:
            redis_client.expire(key, FAILURE_WINDOW_SECONDS)

        return count
    except redis.RedisError as exc:
        print(f"Redis error while registering monitor failure: {exc}")
        return None


def clear_failures(monitor_id: int) -> bool:
    """Start a fresh failure window after an incident is resolved."""
    try:
        redis_client.delete(failure_key(monitor_id))
        return True
    except redis.RedisError as exc:
        print(f"Redis error while clearing monitor failures: {exc}")
        return False
