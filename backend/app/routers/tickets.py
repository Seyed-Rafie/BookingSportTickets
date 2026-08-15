import json
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Query, HTTPException, status

from app.schemas.ticket import TicketSummarySchema, TicketDetailSchema
from app.core.database import execute_query
from app.core.redis_client import get_cache, set_cache
from app.core.elasticsearch import es_client, TICKETS_INDEX

router = APIRouter(prefix="/tickets", tags=["Tickets & Matches"])

# شناسه‌های ثابت انواع ورزش (باید با جدول SPORT_TYPES همخوانی داشته باشد)
SPORT_FOOTBALL_ID = 1
SPORT_VOLLEYBALL_ID = 2
SPORT_BASKETBALL_ID = 3


# =====================================================================
# API شماره ۵: جستجو و فیلتر پیشرفته بلیت‌ها
# =====================================================================


@router.get("/", response_model=List[TicketSummarySchema])
async def search_tickets(
    q: Optional[str] = Query(None, description="عبارت جستجوی متنی (نام تیم، ورزشگاه و...)"),
    sport_type_id: Optional[int] = Query(None, description="شناسه نوع ورزش"),
    city_id: Optional[int] = Query(None, description="شناسه شهر"),
    category_id: Optional[int] = Query(None, description="شناسه دسته‌بندی بلیط"),
    min_price: Optional[float] = Query(None, description="حداقل قیمت"),
    max_price: Optional[float] = Query(None, description="حداکثر قیمت"),
    date_from: Optional[datetime] = Query(None, description="از تاریخ"),
    date_to: Optional[datetime] = Query(None, description="تا تاریخ"),
):
    # ۱. تولید کلید کش Redis متناسب با تمام پارامترها (از جمله q)
    df_str = date_from.isoformat() if date_from else ""
    dt_str = date_to.isoformat() if date_to else ""

    cache_key = (
        f"tickets:search:q_{q}:"
        f"s_{sport_type_id}:c_{city_id}:cat_{category_id}:"
        f"pmin_{min_price}:pmax_{max_price}:df_{df_str}:dt_{dt_str}"
    )

    # ۲. بررسی Redis Cache
    cached_data = get_cache(cache_key)
    if cached_data:
        return json.loads(cached_data)

    # ۳. ساخت کوئری Elastic DSL
    must_conditions = []
    
    # فیلترهای ثابت: فقط بلیط‌های موجود (available) و دارای ظرفیت
    filter_conditions = [
        {"term": {"ticket_status": "available"}},
        {"range": {"remaining_capacity": {"gt": 0}}}
    ]

    # ۴. جستجوی متنی (Fuzzy Search روی عنوان، تیم‌ها و ورزشگاه)
    if q:
        must_conditions.append({
            "multi_match": {
                "query": q,
                "fields": ["title^3", "home_team^2", "away_team^2", "venue_name"],
                "fuzziness": "AUTO"
            }
        })

    # ۵. اعمال فیلترهای شناسه و مشخصات دقیق
    if sport_type_id is not None:
        filter_conditions.append({"term": {"sport_type_id": sport_type_id}})

    if city_id is not None:
        filter_conditions.append({"term": {"city_id": city_id}})

    if category_id is not None:
        filter_conditions.append({"term": {"category_id": category_id}})

    # ۶. فیلتر بازه قیمت
    if min_price is not None or max_price is not None:
        price_range = {}
        if min_price is not None:
            price_range["gte"] = min_price
        if max_price is not None:
            price_range["lte"] = max_price
        filter_conditions.append({"range": {"price": price_range}})

    # ۷. فیلتر بازه تاریخ برگزاری مسابقه
    if date_from or date_to:
        date_range = {}
        if date_from:
            date_range["gte"] = date_from.isoformat()
        if date_to:
            date_range["lte"] = date_to.isoformat()
        filter_conditions.append({"range": {"event_date": date_range}})

    # ترکیب نهایی بدنه کوئری
    query_body = {
        "query": {
            "bool": {
                "must": must_conditions if must_conditions else [{"match_all": {}}],
                "filter": filter_conditions
            }
        },
        "sort": [
            {"event_date": {"order": "asc"}}  # مرتب‌سازی صعودی بر اساس تاریخ مسابقه
        ]
    }

    # ۸. اجرای کوئری در Elasticsearch
    es_response = await es_client.search(
        index=TICKETS_INDEX,
        body=query_body,
        size=100  # تعداد حداکثر نتایج دریافتی
    )

    hits = es_response["hits"]["hits"]

    # ۹. تبدیل سندهای دریافت شده از Elastic به ساختار پاسخ API (TicketSummarySchema)
    formatted_response = []
    for hit in hits:
        source = hit["_source"]
        item = {
            "ticket_id": source.get("ticket_id"),
            "ticket_code": source.get("ticket_code"),
            "category_name": source.get("category_name", ""),
            "price": source.get("price"),
            "remaining_capacity": source.get("remaining_capacity"),
            "status": source.get("ticket_status"),
            "match": {
                "match_id": source.get("match_id"),
                "competition_name": source.get("competition_name") or "نامشخص",
                "sport_type_name": source.get("sport_type", ""),
                "home_team": {
                    "team_id": source.get("home_team_id") or 0,
                    "name": source.get("home_team", ""),
                },
                "away_team": {
                    "team_id": source.get("away_team_id") or 0,
                    "name": source.get("away_team", ""),
                },
                "venue_name": source.get("venue_name", ""),
                "city_name": source.get("city", ""),
                "match_datetime": source.get("event_date"),
                "status": source.get("match_status", ""),
            },
        }
        formatted_response.append(item)

    # ۱۰. ذخیره نتیجه در کش Redis
    set_cache(
        cache_key,
        json.dumps(formatted_response, ensure_ascii=False, default=str),
        ttl_seconds=300,
    )

    return formatted_response


# =====================================================================
# API شماره ۶: دریافت جزئیات کامل یک بلیت مشخص (یکبار و اصلاح‌شده)
# =====================================================================


@router.get("/{ticket_id}", response_model=TicketDetailSchema)
def get_ticket_detail(ticket_id: int):

    # 1. Cache Key
    cache_key = f"ticket_detail:{ticket_id}"

    # 2. بررسی Redis
    cached_data = get_cache(cache_key)
    if cached_data:
        return json.loads(cached_data)

    # 3. اطلاعات اصلی بلیت و مسابقه
    ticket_sql = """
        SELECT
            t.ticket_id,
            t.ticket_code,
            t.price,
            t.remaining_capacity,
            t.status AS ticket_status,

            tc.name AS category_name,

            m.match_id,
            m.match_datetime,
            m.status AS match_status,
            m.sport_type_id,

            st.name AS sport_type_name,
            comp.name AS competition_name,

            ht.team_id AS home_team_id,
            ht.name AS home_team_name,

            at.team_id AS away_team_id,
            at.name AS away_team_name,

            v.name AS venue_name,
            c.name AS city_name

        FROM TICKETS t
        INNER JOIN MATCHES m ON t.match_id = m.match_id
        INNER JOIN SPORT_TYPES st ON m.sport_type_id = st.sport_type_id
        INNER JOIN COMPETITIONS comp ON m.competition_id = comp.competition_id
        INNER JOIN TEAMS ht ON m.home_team_id = ht.team_id
        INNER JOIN TEAMS at ON m.away_team_id = at.team_id
        INNER JOIN VENUES v ON m.venue_id = v.venue_id
        INNER JOIN CITIES c ON v.city_id = c.city_id
        INNER JOIN TICKET_CATEGORIES tc ON t.category_id = tc.category_id
            AND tc.sport_type_id = m.sport_type_id

        WHERE t.ticket_id = %s;
    """

    db_rows = execute_query(ticket_sql, (ticket_id,), fetch_all=True)

    if not db_rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="بلیت مورد نظر یافت نشد."
        )

    row = db_rows[0]

    # 4. امکانات بلیت (Facilities)
    facilities_sql = """
        SELECT f.name
        FROM FACILITIES f
        INNER JOIN TICKET_FACILITIES tf ON f.facility_id = tf.facility_id
        WHERE tf.ticket_id = %s;
    """
    facilities_rows = execute_query(facilities_sql, (ticket_id,), fetch_all=True)
    facilities_list = [f["name"] for f in facilities_rows]

    # 5. دریافت جزئیات اختصاصی بر اساس sport_type_id (به جای بررسی رشته‌ای)
    current_sport_id = row["sport_type_id"]
    football_details = None
    volleyball_details = None
    basketball_details = None

    if current_sport_id == SPORT_FOOTBALL_ID:
        q = "SELECT gate_number, has_parking, vip_services FROM FOOTBALL_DETAILS WHERE ticket_id = %s;"
        res = execute_query(q, (ticket_id,), fetch_all=True)
        football_details = res[0] if res else None

    elif current_sport_id == SPORT_VOLLEYBALL_ID:
        q = "SELECT entrance_gate, special_services FROM VOLLEYBALL_DETAILS WHERE ticket_id = %s;"
        res = execute_query(q, (ticket_id,), fetch_all=True)
        volleyball_details = res[0] if res else None

    elif current_sport_id == SPORT_BASKETBALL_ID:
        q = "SELECT entrance_gate, vip_services, has_food_court FROM BASKETBALL_DETAILS WHERE ticket_id = %s;"
        res = execute_query(q, (ticket_id,), fetch_all=True)
        basketball_details = res[0] if res else None

    # 6. ساخت Response نهایی
    response_data = {
        "ticket_id": row["ticket_id"],
        "ticket_code": row["ticket_code"],
        "category_name": row["category_name"],
        "price": row["price"],
        "remaining_capacity": row["remaining_capacity"],
        "status": row["ticket_status"],
        "match": {
            "match_id": row["match_id"],
            "competition_name": row["competition_name"],
            "sport_type_name": row["sport_type_name"],
            "home_team": {
                "team_id": row["home_team_id"],
                "name": row["home_team_name"],
            },
            "away_team": {
                "team_id": row["away_team_id"],
                "name": row["away_team_name"],
            },
            "venue_name": row["venue_name"],
            "city_name": row["city_name"],
            "match_datetime": row["match_datetime"],
            "status": row["match_status"],
        },
        "facilities": facilities_list,
        "football_details": football_details,
        "volleyball_details": volleyball_details,
        "basketball_details": basketball_details,
    }

    # 7. ذخیره در Redis برای 10 دقیقه
    set_cache(
        cache_key,
        json.dumps(response_data, ensure_ascii=False, default=str),
        ttl_seconds=600,
    )

    return response_data
