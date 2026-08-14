# به‌جای ایمپورت redis_instance، توابع کمکی را ایمپورت کنید
from app.core.redis_client import redis_client, clear_cache_pattern


def invalidate_ticket_cache(ticket_id: int = None) -> None:
    """پاک‌سازی کش بلیت‌ها با استفاده از توابع کمکی redis_client"""
    try:
        # ۱. پاک‌سازی بلیت خاص
        if ticket_id and redis_client:
            redis_client.delete(f"ticket_detail:{ticket_id}")
            
        # ۲. پاک‌سازی تمام کلیدهای جستجوی بلیت با تابع آماده و امن خودتان
        clear_cache_pattern("tickets:*")
        
    except Exception as e:
        print(f"[Cache Error] Invalidate ticket cache failed: {e}")


def invalidate_venue_cache() -> None:
    """پاک‌سازی کش ورزشگاه‌ها"""
    try:
        clear_cache_pattern("venues:*")
    except Exception as e:
        print(f"[Cache Error] Invalidate venue cache failed: {e}")