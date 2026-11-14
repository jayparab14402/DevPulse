import json
import os
import time

import redis
import requests
from dotenv import load_dotenv
from .services.incident_service import handle_incident

load_dotenv()

REDIS_URL = os.environ["REDIS_URL"]

redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True
)


def register_failure(monitor_id):
    try:
        key = f"monitors:{monitor_id}:failures"

        redis_client.incr(key)

        count = redis_client.get(key)

        res = handle_incident(conn, monitor_id, count)

        if int(count) == 3:
            redis_client.expire(key, 300)



    except redis.RedisError as e:
        print(f"Redis error: {e}")


register_failure(12)



print(redis_client.ping())