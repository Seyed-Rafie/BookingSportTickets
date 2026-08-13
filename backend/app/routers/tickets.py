import json
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Query, HTTPException, status

from app.schemas.ticket import TicketSummarySchema, TicketDetailSchema
from app.core.database import execute_query
from app.core.redis_client import get_cache, set_cache


router = APIRouter(
    prefix="/tickets",
    tags=["Tickets & Matches"]
)


# =====================================================================
# API شماره ۵: جستجو و فیلتر پیشرفته بلیت‌ها
# =====================================================================

@router.get("/", response_model=List[TicketSummarySchema])
def search_tickets(
    sport_type_id: Optional[int] = Query(
        None,
        description="شناسه نوع ورزش"
    ),
    city_id: Optional[int] = Query(
        None,
        description="شناسه شهر"
    ),
    category_id: Optional[int] = Query(
        None,
        description="شناسه دسته‌بندی بلیط"
    ),
    min_price: Optional[float] = Query(
        None,
        description="حداقل قیمت"
    ),
    max_price: Optional[float] = Query(
        None,
        description="حداکثر قیمت"
    ),
    date_from: Optional[datetime] = Query(
        None,
        description="از تاریخ"
    ),
    date_to: Optional[datetime] = Query(
        None,
        description="تا تاریخ"
    )
):
    # 1. تولید کلید کش
    cache_key = (
        f"tickets:"
        f"s_{sport_type_id}:"
        f"c_{city_id}:"
        f"cat_{category_id}:"
        f"pmin_{min_price}:"
        f"pmax_{max_price}:"
        f"df_{date_from}:"
        f"dt_{date_to}"
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

        INNER JOIN MATCHES m
            ON t.match_id = m.match_id

        INNER JOIN SPORT_TYPES st
            ON m.sport_type_id = st.sport_type_id

        INNER JOIN COMPETITIONS comp
            ON m.competition_id = comp.competition_id

        INNER JOIN TEAMS ht
            ON m.home_team_id = ht.team_id

        INNER JOIN TEAMS at
            ON m.away_team_id = at.team_id

        INNER JOIN VENUES v
            ON m.venue_id = v.venue_id

        INNER JOIN CITIES c
            ON v.city_id = c.city_id

        INNER JOIN TICKET_CATEGORIES tc
            ON t.category_id = tc.category_id
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

    # 5. اضافه کردن شرایط
    if conditions:
        base_sql += " AND " + " AND ".join(conditions)

    # 6. مرتب‌سازی
    base_sql += " ORDER BY m.match_datetime ASC;"

    # 7. اجرای Query
    db_rows = execute_query(
        base_sql,
        tuple(params)
    )

    # 8. ساخت Response
    formatted_response = []

    for row in db_rows:
        item = {
            "ticket_id": row["ticket_id"],
            "ticket_code": row["ticket_code"],
            "category_name": row["category_name"],
            "price": float(row["price"]),
            "remaining_capacity": row["remaining_capacity"],
            "status": row["ticket_status"],

            "match": {
                "match_id": row["match_id"],
                "competition_name": row["competition_name"],
                "sport_type_name": row["sport_type_name"],

                "home_team": {
                    "team_id": row["home_team_id"],
                    "name": row["home_team_name"]
                },

                "away_team": {
                    "team_id": row["away_team_id"],
                    "name": row["away_team_name"]
                },

                "venue_name": row["venue_name"],
                "city_name": row["city_name"],
                "match_datetime": row["match_datetime"].isoformat(),
                "status": row["match_status"]
            }
        }

        formatted_response.append(item)

    # 9. ذخیره در Redis برای 5 دقیقه
    set_cache(
        cache_key,
        json.dumps(
            formatted_response,
            ensure_ascii=False
        ),
        ttl_seconds=300
    )

    return formatted_response


# =====================================================================
# API شماره ۶: دریافت جزئیات کامل یک بلیت مشخص
# =====================================================================

@router.get(
    "/{ticket_id}",
    response_model=TicketDetailSchema
)
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

        INNER JOIN MATCHES m
            ON t.match_id = m.match_id

        INNER JOIN SPORT_TYPES st
            ON m.sport_type_id = st.sport_type_id

        INNER JOIN COMPETITIONS comp
            ON m.competition_id = comp.competition_id

        INNER JOIN TEAMS ht
            ON m.home_team_id = ht.team_id

        INNER JOIN TEAMS at
            ON m.away_team_id = at.team_id

        INNER JOIN VENUES v
            ON m.venue_id = v.venue_id

        INNER JOIN CITIES c
            ON v.city_id = c.city_id

        INNER JOIN TICKET_CATEGORIES tc
            ON t.category_id = tc.category_id
            AND tc.sport_type_id = m.sport_type_id

        WHERE t.ticket_id = %s;
    """

    db_rows = execute_query(
        ticket_sql,
        (ticket_id,)
    )

    # 4. اگر بلیت پیدا نشد
    if not db_rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="بلیت مورد نظر یافت نشد."
        )

    row = db_rows[0]

    # 5. امکانات بلیت
    facilities_sql = """
        SELECT f.name
        FROM FACILITIES f
        INNER JOIN TICKET_FACILITIES tf
            ON f.facility_id = tf.facility_id
        WHERE tf.ticket_id = %s;
    """

    facilities_rows = execute_query(
        facilities_sql,
        (ticket_id,)
    )

    facilities_list = [
        facility["name"]
        for facility in facilities_rows
    ]

    # 6. تشخیص نوع ورزش
    sport_name = row["sport_type_name"].strip().lower()

    football_details = None
    volleyball_details = None
    basketball_details = None

    # ---------------------------------------------------------------
    # Football
    # ---------------------------------------------------------------

    if sport_name in ["football", "فوتبال"]:

        football_sql = """
            SELECT
                gate_number,
                has_parking,
                vip_services
            FROM FOOTBALL_DETAILS
            WHERE ticket_id = %s;
        """

        football_rows = execute_query(
            football_sql,
            (ticket_id,)
        )

        if football_rows:
            football_details = {
                "gate_number": football_rows[0]["gate_number"],
                "has_parking": football_rows[0]["has_parking"],
                "vip_services": football_rows[0]["vip_services"]
            }

    # ---------------------------------------------------------------
    # Volleyball
    # ---------------------------------------------------------------

    elif sport_name in ["volleyball", "والیبال"]:

        volleyball_sql = """
            SELECT
                entrance_gate,
                special_services
            FROM VOLLEYBALL_DETAILS
            WHERE ticket_id = %s;
        """

        volleyball_rows = execute_query(
            volleyball_sql,
            (ticket_id,)
        )

        if volleyball_rows:
            volleyball_details = {
                "entrance_gate": volleyball_rows[0]["entrance_gate"],
                "special_services": volleyball_rows[0]["special_services"]
            }

    # ---------------------------------------------------------------
    # Basketball
    # ---------------------------------------------------------------

    elif sport_name in ["basketball", "بسکتبال"]:

        basketball_sql = """
            SELECT
                entrance_gate,
                vip_services,
                has_food_court
            FROM BASKETBALL_DETAILS
            WHERE ticket_id = %s;
        """

        basketball_rows = execute_query(
            basketball_sql,
            (ticket_id,)
        )

        if basketball_rows:
            basketball_details = {
                "entrance_gate": basketball_rows[0]["entrance_gate"],
                "vip_services": basketball_rows[0]["vip_services"],
                "has_food_court": basketball_rows[0]["has_food_court"]
            }

    # 7. ساخت Response نهایی
    response_data = {
        "ticket_id": row["ticket_id"],
        "ticket_code": row["ticket_code"],
        "category_name": row["category_name"],
        "price": float(row["price"]),
        "remaining_capacity": row["remaining_capacity"],
        "status": row["ticket_status"],

        "match": {
            "match_id": row["match_id"],
            "competition_name": row["competition_name"],
            "sport_type_name": row["sport_type_name"],

            "home_team": {
                "team_id": row["home_team_id"],
                "name": row["home_team_name"]
            },

            "away_team": {
                "team_id": row["away_team_id"],
                "name": row["away_team_name"]
            },

            "venue_name": row["venue_name"],
            "city_name": row["city_name"],
            "match_datetime": row["match_datetime"].isoformat(),
            "status": row["match_status"]
        },

        "facilities": facilities_list,

        "football_details": football_details,
        "volleyball_details": volleyball_details,
        "basketball_details": basketball_details
    }

    # 8. ذخیره در Redis برای 10 دقیقه
    set_cache(
        cache_key,
        json.dumps(
            response_data,
            ensure_ascii=False
        ),
        ttl_seconds=600
    )

    return response_data