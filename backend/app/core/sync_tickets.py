import asyncio
from datetime import datetime, date
from decimal import Decimal
from psycopg2.extras import RealDictCursor
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
from app.core.database import execute_query

from app.core.elasticsearch import (
    es_client,
    TICKETS_INDEX,
    init_es_index
)



def fetch_tickets_from_postgres():
    """
    اجرای کوئری JOIN جهت استخراج کامل داده‌های بلیط از PostgreSQL
    """

    query = """
        SELECT 
            t.ticket_id,
            t.ticket_code,
            t.match_id,
            t.category_id,
            t.total_capacity,
            t.remaining_capacity,
            t.price,
            t.status AS ticket_status,
            m.match_datetime AS event_date,
            m.status AS match_status,
            m.sport_type_id,
            m.home_team_id,
            m.away_team_id,
            v.city_id,
            v.name AS venue_name,
            v.address AS venue_address,
            tc.name AS category_name,
            st.name AS sport_type,
            ci.name AS city,
            ht.name AS home_team,
            at.name AS away_team,
            comp.name AS competition_name,
            CONCAT(COALESCE(ht.name, ''), ' - ', COALESCE(at.name, '')) AS title
        FROM TICKETS t
        JOIN MATCHES m ON t.match_id = m.match_id
        JOIN VENUES v ON m.venue_id = v.venue_id
        JOIN TICKET_CATEGORIES tc ON t.category_id = tc.category_id
        LEFT JOIN TEAMS ht ON m.home_team_id = ht.team_id
        LEFT JOIN TEAMS at ON m.away_team_id = at.team_id
        LEFT JOIN SPORT_TYPES st ON m.sport_type_id = st.sport_type_id
        LEFT JOIN CITIES ci ON v.city_id = ci.city_id
        LEFT JOIN COMPETITIONS comp ON m.competition_id = comp.competition_id;
    """
    records = execute_query(query, fetch_all=True)
    return records


def transform_record(record: dict) -> dict:
    """
    اصلاح انواع داده غیرقابل سریالایز در JSON (تاریخ و اعداد Decimal)
    """
    # تبدیل Decimal پایتون به float
    if isinstance(record.get("price"), Decimal):
        record["price"] = float(record["price"])

    # تبدیل datetime یا date به فرمت استاندارد ISO 8601
    if isinstance(record.get("event_date"), (datetime, date)):
        record["event_date"] = record["event_date"].isoformat()

    # جایگزینی عنوان فرضی در صورت خالی بودن نام تیم‌ها
    if not record.get("title") or record.get("title").strip() == "-":
        record["title"] = f"مسابقه شماره {record.get('match_id')}"

    return record


def generate_bulk_actions(records: list):
    """
    ساخت ساختار اکشن‌های دسته جمعی برای async_bulk
    """
    for record in records:
        doc = transform_record(record)
        yield {
            "_index": TICKETS_INDEX,
            "_id": str(doc["ticket_id"]),
            "_source": doc
        }


async def main():
    print("=== شروع عملیات همگام‌سازی بلیط‌ها از PostgreSQL به Elasticsearch ===")
    
    # ۱. اطمینان از ایجاد ایندکس و MAPPING در Elastic
    await init_es_index()

    # ۲. دریافت داده‌ها از PostgreSQL
    print("[1/3] در حال دریافت داده‌ها از PostgreSQL (Neon)...")
    try:
        tickets = fetch_tickets_from_postgres()
        print(f"-> تعداد {len(tickets)} بلیط با موفقیت استخراج شد.")
    except Exception as e:
        print(f"[خطا] عدم موفقیت در دریافت داده از دیتابیس: {e}")
        return

    if not tickets:
        print("هیچ بلیطی در دیتابیس یافت نشد.")
        return

    # ۳. ارسال دسته‌ای به Elasticsearch (Bonsai)
    print("[2/3] در حال ارسال داده‌ها به‌صورت دسته‌ای به Elasticsearch...")
    try:
        success_count, failed = await async_bulk(
            client=es_client,
            actions=generate_bulk_actions(tickets),
            refresh=True
        )
        print(f"[3/3] عملیات با موفقیت انجام شد!")
        print(f"-> تعداد سندهای ثبت‌شده در Elastic: {success_count}")
        if failed:
            print(f"-> تعداد خطاها: {len(failed)}")
    except Exception as e:
        print(f"[خطا] خطا در تزریق دسته‌ای داده‌ها به Elasticsearch: {e}")
    finally:
        await es_client.close()

if __name__ == "__main__":
    asyncio.run(main())