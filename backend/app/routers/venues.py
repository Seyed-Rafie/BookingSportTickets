import json
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, status

from app.schemas.venue import VenueResponseSchema
from app.core.database import execute_query
from app.core.redis_client import get_cache, set_cache

router = APIRouter(prefix="/venues", tags=["Venues & Cities"])

@router.get("/", response_model=List[VenueResponseSchema])
def get_venues(
    province_id: Optional[int] = Query(None, description="فیلتر بر اساس شناسه استان"),
    city_id: Optional[int] = Query(None, description="فیلتر بر اساس شناسه شهر"),
    search: Optional[str] = Query(None, description="جستجو در نام ورزشگاه یا آدرس")
):
    # ۱. ساخت کلید اختصاصی و یکتا برای کش Redis
    clean_search = search.strip().lower() if search else "none"
    cache_key = f"venues:p_{province_id}:c_{city_id}:q_{clean_search}"

    # ۲. بررسی حضور داده در Redis (Cache Read)
    cached_data = get_cache(cache_key)
    if cached_data:
        # اگر داده در کش باشد، مستقیماً همان را برمی‌گردانیم
        return json.loads(cached_data)

    # ۳. ساخت کوئری پایه SQL با استفاده از JOIN سه جدول
    base_sql = """
        SELECT 
            v.venue_id,
            v.name AS venue_name,
            v.address,
            v.capacity,
            c.city_id,
            c.name AS city_name,
            p.province_id,
            p.name AS province_name
        FROM VENUES v
        INNER JOIN CITIES c ON v.city_id = c.city_id
        INNER JOIN PROVINCES p ON c.province_id = p.province_id
    """
    
    conditions = []
    params = []

    # ۴. ساخت شرط‌های دینامیک بر اساس ورودی‌های کاربر
    if province_id is not None:
        conditions.append("p.province_id = %s")
        params.append(province_id)

    if city_id is not None:
        conditions.append("c.city_id = %s")
        params.append(city_id)

    if search:
        conditions.append("(v.name ILIKE %s OR v.address ILIKE %s)")
        search_param = f"%{search.strip()}%"
        params.extend([search_param, search_param])

    # ترکیب شرط‌ها با WHERE در صورت وجود
    if conditions:
        base_sql += " WHERE " + " AND ".join(conditions)

    base_sql += " ORDER BY v.venue_id ASC;"

    # ۵. اجرای کوئری خام روی PostgreSQL
    try:
        db_rows = execute_query(base_sql, tuple(params))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query failed: {str(e)}"
        )

    # ۶. نگاشت سطرهای تخت دیتابیس به ساختار درختی (Data Mapping)
    formatted_response = []
    for row in db_rows:
        venue_item = {
            "venue_id": row["venue_id"],
            "name": row["venue_name"],
            "address": row["address"],
            "capacity": row["capacity"],
            "city": {
                "city_id": row["city_id"],
                "name": row["city_name"],
                "province": {
                    "province_id": row["province_id"],
                    "name": row["province_name"]
                }
            }
        }
        formatted_response.append(venue_item)

    # ۷. ذخیره‌سازی نتیجه در Redis با زمان انقضای ۱ ساعت (TTL = 3600)
    set_cache(cache_key, json.dumps(formatted_response, ensure_ascii=False), ttl_seconds=3600)

    return formatted_response