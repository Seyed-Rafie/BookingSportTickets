import json
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Query, HTTPException, status

from app.schemas.ticket import TicketSummarySchema, TicketDetailSchema
from app.core.database import execute_query
from app.core.redis_client import get_cache, set_cache

router = APIRouter(prefix="/tickets", tags=["Tickets & Matches"])

# شناسه‌های ثابت انواع ورزش (باید با جدول SPORT_TYPES همخوانی داشته باشد)
SPORT_FOOTBALL_ID = 1
SPORT_VOLLEYBALL_ID = 2
SPORT_BASKETBALL_ID = 3


# =====================================================================
# API شماره ۵: جستجو و فیلتر پیشرفته بلیت‌ها
# =====================================================================


@router.get("/", response_model=List[TicketSummarySchema])
def search_tickets(
    sport_type_id: Optional[int] = Query(None, description="شناسه نوع ورزش"),
    city_id: Optional[int] = Query(None, description="شناسه شهر"),
    category_id: Optional[int] = Query(None, description="شناسه دسته‌بندی بلیط"),
    min_price: Optional[float] = Query(None, description="حداقل قیمت"),
    max_price: Optional[float] = Query(None, description="حداکثر قیمت"),
    date_from: Optional[datetime] = Query(None, description="از تاریخ"),
    date_to: Optional[datetime] = Query(None, description="تا تاریخ"),
):
    # 1. تولید کلید کش ایمن و استاندارد
    df_str = date_from.isoformat() if date_from else ""
    dt_str = date_to.isoformat() if date_to else ""

    cache_key = (
        f"tickets:search:"
        f"s_{sport_type_id}:c_{city_id}:cat_{category_id}:"
        f"pmin_{min_price}:pmax_{max_price}:df_{df_str}:dt_{dt_str}"
    )

    # 2. بررسی Redis Cache
    cached_data = get_cache(cache_key)
    if cached_data:
        return json.loads(cached_data)

    # 3. کوئری اصلی
    base_sql = """
        SELECT
            t.ticket_id,
            t.ticket_code,
            tc.name AS category_name,
            t.price,
            t.remaining_capacity,
            t.status AS ticket_status,

            m.match_id,
            m.match_datetime,
            m.status AS match_status,

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

        WHERE
            t.status = 'available'
            AND t.remaining_capacity > 0
    """

    # 4. شرایط فیلتر
    conditions = []
    params = []

    if sport_type_id is not None:
        conditions.append("m.sport_type_id = %s")
        params.append(sport_type_id)

    if city_id is not None:
        conditions.append("v.city_id = %s")
        params.append(city_id)

    if category_id is not None:
        conditions.append("t.category_id = %s")
        params.append(category_id)

    if min_price is not None:
        conditions.append("t.price >= %s")
        params.append(min_price)

    if max_price is not None:
        conditions.append("t.price <= %s")
        params.append(max_price)

    if date_from is not None:
        conditions.append("m.match_datetime >= %s")
        params.append(date_from)

    if date_to is not None:
        conditions.append("m.match_datetime <= %s")
        params.append(date_to)

    if conditions:
        base_sql += " AND " + " AND ".join(conditions)

    base_sql += " ORDER BY m.match_datetime ASC;"

    # 5. اجرای Query
    db_rows = execute_query(base_sql, tuple(params))

    # 6. ساخت Response
    formatted_response = []
    for row in db_rows:
        item = {
            "ticket_id": row["ticket_id"],
            "ticket_code": row["ticket_code"],
            "category_name": row["category_name"],
            "price": row["price"],  # تبدیل به float حذف شد تا Decimal/Int حفظ شود
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
        }
        formatted_response.append(item)

    # 7. ذخیره در Redis (با default=str برای سریالایز شدن راحت datetime و decimal)
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

    db_rows = execute_query(ticket_sql, (ticket_id,))

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
    facilities_rows = execute_query(facilities_sql, (ticket_id,))
    facilities_list = [f["name"] for f in facilities_rows]

    # 5. دریافت جزئیات اختصاصی بر اساس sport_type_id (به جای بررسی رشته‌ای)
    current_sport_id = row["sport_type_id"]
    football_details = None
    volleyball_details = None
    basketball_details = None

    if current_sport_id == SPORT_FOOTBALL_ID:
        q = "SELECT gate_number, has_parking, vip_services FROM FOOTBALL_DETAILS WHERE ticket_id = %s;"
        res = execute_query(q, (ticket_id,))
        football_details = res[0] if res else None

    elif current_sport_id == SPORT_VOLLEYBALL_ID:
        q = "SELECT entrance_gate, special_services FROM VOLLEYBALL_DETAILS WHERE ticket_id = %s;"
        res = execute_query(q, (ticket_id,))
        volleyball_details = res[0] if res else None

    elif current_sport_id == SPORT_BASKETBALL_ID:
        q = "SELECT entrance_gate, vip_services, has_food_court FROM BASKETBALL_DETAILS WHERE ticket_id = %s;"
        res = execute_query(q, (ticket_id,))
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
