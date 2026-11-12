import redis
import os
from dotenv import load_dotenv

load_dotenv()

env = os.environ["REDIS_URL"]
print(env)

connect = redis.Redis.from_url(env, decode_responses=True)

def register_failure(monitor_id):
    key = f"monitor:{monitor_id}:failures"

    count = connect.incr(key)

    if count == 1:
        connect.expire(key, 60)

    print(f"COUNT DATA {count} -----------------------------------")

    return count

# res = register_failure(connect, 13)
# print(res)












# connect = redis.Redis.from_url(env, decode_responses=True)

# def register_failure(connect, monitor_id):
#     try:
#         key = f"monitor:{monitor_id}:failures"

#         # connect.incr(key)

#         count = connect.get(key)
#         print(count)

#     except redis.RedisError as e:
#         print(f"Redis error: {e}")


# register_failure(connect, 12)



# print(connect.ping())