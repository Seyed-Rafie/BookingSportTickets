import json
import redis
from typing import Any, Optional
from app.core.config import settings

# create Redis client
# decode_responses=True, is for returning data in str form, not bytes
try:
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    print("connected to redis successfully")
except Exception as e:
    print(f"error with connection to redis: {e}")
    redis_client = None


# ==========================================
# 1. managing OTP (one-time password)
# ==========================================

def set_otp(phone: str, code: str, ttl_seconds: int = 120) -> bool:
    if not redis_client:
        return False
    key = f"otp:{phone}"
    return redis_client.setex(key, ttl_seconds, code)


def get_otp(phone: str) -> Optional[str]:
    if not redis_client:
        return None
    key = f"otp:{phone}"
    return redis_client.get(key)


def delete_otp(phone: str) -> bool:
    # delete code after like successful use
    if not redis_client:
        return False
    key = f"otp:{phone}"
    return redis_client.delete(key) > 0


# ==========================================
# 2. manage Caching
# ==========================================

def set_cache(key: str, data: Any, ttl_seconds: int = 300) -> bool:
    # save data to cash with 5 minutes ttl (time to live)
    if not redis_client:
        return False
    try:
        json_data = json.dumps(data, ensure_ascii=False)
        return redis_client.setex(key, ttl_seconds, json_data)
    except Exception as e:
        print(f"error in saving cash in redis: {e}")
        return False


def get_cache(key: str) -> Optional[Any]:
    # getting cash and convert it to dictionary
    if not redis_client:
        return None
    try:
        cached_val = redis_client.get(key)
        if cached_val:
            return json.loads(cached_val)
        return None
    except Exception as e:
        print(f"error in read cash in redis: {e}")
        return None


def clear_cache_pattern(pattern: str) -> int:
    # delete cash by pattern (like ticket:*, delete all data for tickets)
    if not redis_client:
        return 0
    try:
        keys = redis_client.keys(pattern)
        if keys:
            return redis_client.delete(*keys)
        return 0
    except Exception as e:
        print(f"error with deleteing cash with tihs pattern ({pattern}): {e}")
        return 0


# ==========================================
# ۳. checking redis health 
# ==========================================

def check_redis_health() -> bool:
    # checking health redis with ping() function
    if not redis_client:
        return False
    try:
        return redis_client.ping()
    except Exception as e:
        print(f"error in check Redis health: {e}")
        return False