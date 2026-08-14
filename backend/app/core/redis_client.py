import json
import logging
import redis
from typing import Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# ایجاد کلاینت Redis و تست اتصال واقعی
try:
    redis_client: Optional[redis.Redis] = redis.from_url(
        settings.REDIS_URL, decode_responses=True
    )
    # تست واقعی شبکه جهت اطمینان از بالا بودن Redis
    redis_client.ping()
    logger.info("Connected to Redis successfully.")
except Exception as e:
    logger.error(f"Error connecting to Redis: {e}")
    redis_client = None


# ==========================================
# ۱. مدیریت کد یک‌بار مصرف (OTP)
# ==========================================

def set_otp(phone: str, code: str, ttl_seconds: int = 120) -> bool:
    if not redis_client:
        return False
    key = f"otp:{phone}"
    try:
        return bool(redis_client.setex(key, ttl_seconds, code))
    except Exception as e:
        logger.error(f"Error setting OTP for {phone}: {e}")
        return False


def get_otp(phone: str) -> Optional[str]:
    if not redis_client:
        return None
    key = f"otp:{phone}"
    try:
        return redis_client.get(key)
    except Exception as e:
        logger.error(f"Error getting OTP for {phone}: {e}")
        return None


def delete_otp(phone: str) -> bool:
    if not redis_client:
        return False
    key = f"otp:{phone}"
    try:
        return bool(redis_client.delete(key) > 0)
    except Exception as e:
        logger.error(f"Error deleting OTP for {phone}: {e}")
        return False


# ==========================================
# ۲. مدیریت کش (Caching)
# ==========================================

def set_cache(key: str, data: Any, ttl_seconds: int = 300) -> bool:
    if not redis_client:
        return False
    try:
        json_data = json.dumps(data, ensure_ascii=False)
        return bool(redis_client.setex(key, ttl_seconds, json_data))
    except Exception as e:
        logger.error(f"Error setting cache for key '{key}': {e}")
        return False


def get_cache(key: str) -> Optional[Any]:
    if not redis_client:
        return None
    try:
        cached_val = redis_client.get(key)
        if isinstance(cached_val, str):
            return json.loads(cached_val)
        return None
    except Exception as e:
        logger.error(f"Error reading cache for key '{key}': {e}")
        return None


def clear_cache_pattern(pattern: str) -> int:
  """حذف امن کلیدها بر اساس الگوی الگوریتمی به جای استفاده از KEYS"""
  if not redis_client:
    return 0
  try:
    deleted_count = 0
    pipe = redis_client.pipeline()
    batch_size = 0

    for key in redis_client.scan_iter(match=pattern, count=100):
      pipe.delete(key)
      batch_size += 1

      # اجرای دستورات در دسته‌های ۱۰۰ تایی
      if batch_size >= 100:
        results = (
            pipe.execute()
        )  # خروجی شامل لیست نتایج است (مثلاً [1, 1, 0, 1])
        deleted_count += sum(results)
        batch_size = 0

    # اجرای دسته‌های باقی‌مانده (کمتر از ۱۰۰)
    if batch_size > 0:
      results = pipe.execute()
      deleted_count += sum(results)

    return deleted_count
  except Exception as e:
    # کوتیشن بعد از {pattern} اصلاح شد
    logger.error(f"Error deleting cache pattern '{pattern}': {e}")
    return 0

# ==========================================
# ۳. بررسی سلامت Redis
# ==========================================

def check_redis_health() -> bool:
    if not redis_client:
        return False
    try:
        return bool(redis_client.ping())
    except Exception as e:
        logger.error(f"Error checking Redis health: {e}")
        return False