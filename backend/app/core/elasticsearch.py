# backend/app/core/elasticsearch.py
from typing import Optional, Dict, Any
from elasticsearch import AsyncElasticsearch
from app.core.config import settings
import logging

# ۱. دریافت آدرس کامل Bonsai از فایل .env
ELASTICSEARCH_URL = settings.ELASTICSEARCH_URL

# ۲. ساخت کلاینت (پایتون اتوماتیک Username و Password موجود در URL را شناسایی می‌کند)
es_client = AsyncElasticsearch(ELASTICSEARCH_URL)

TICKETS_INDEX = "tickets"

logger = logging.getLogger(__name__)

# ۲. تعریف نگاشت (Mapping) دقیق فیلدها جهت ساخت ایندکس
TICKETS_INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "id": {"type": "integer"},
            "title": {"type": "text", "analyzer": "standard"},
            "home_team": {"type": "text"},
            "away_team": {"type": "text"},
            "venue_name": {"type": "text"},
            "city": {"type": "keyword"},
            "sport_type": {"type": "keyword"},
            "price": {"type": "integer"},
            "event_date": {"type": "date"},
            "available_seats": {"type": "integer"},
            "status": {"type": "keyword"}
        }
    }
}

async def check_es_health() -> bool:
    """
    بررسی سلامت اتصال به Elasticsearch و دریافت اطلاعات کلستر
    """
    try:
        # بررسی زنده بودن اتصال
        is_alive = await es_client.ping()
        if is_alive:
            info = await es_client.info()
            return True
        logger.error('error in connecting to elastic search')
        return False
    except Exception as e:
        logger.error(str(e))
        return False


async def get_es_client() -> AsyncElasticsearch:
    """تابع کمکی جهت دریافت کلاینت Elasticsearch در اینجکشن‌های FastAPI"""
    return es_client


async def init_es_index() -> None:
    """
    بررسی وجود ایندکس بلیط‌ها و ایجاد آن در صورت عدم وجود
    (این تابع هنگام استارت خوردن FastAPI در main.py فراخوانی می‌شود)
    """
    try:
        exists = await es_client.indices.exists(index=TICKETS_INDEX)
        if not exists:
            await es_client.indices.create(
                index=TICKETS_INDEX,
                body=TICKETS_INDEX_MAPPING
            )
            print(f"[Elasticsearch] Index '{TICKETS_INDEX}' created successfully.")
    except Exception as e:
        print(f"[Elasticsearch Error] Failed to initialize index: {e}")


def build_ticket_search_query(
    q: Optional[str] = None,
    sport_type: Optional[str] = None,
    city: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    ساخت بدنه کوئری Elastic DSL بر اساس پارامترهای ورودی
    """
    must_conditions = []
    filter_conditions = []

    # ۱. جستجوی متنی (Fuzzy + Multi-field Match)
    if q:
        must_conditions.append({
            "multi_match": {
                "query": q,
                "fields": ["title^3", "home_team^2", "away_team^2", "venue_name"],
                "fuzziness": "AUTO"
            }
        })

    # ۲. فیلترهای دقیق (Exact Matches)
    if sport_type:
        filter_conditions.append({"term": {"sport_type": sport_type}})

    if city:
        filter_conditions.append({"term": {"city": city}})

    # فقط نمایش بلیط‌های فعال
    filter_conditions.append({"term": {"status": "active"}})

    # ۳. فیلتر بازه قیمت
    if min_price is not None or max_price is not None:
        price_range = {}
        if min_price is not None:
            price_range["gte"] = min_price
        if max_price is not None:
            price_range["lte"] = max_price
        filter_conditions.append({"range": {"price": price_range}})

    # ۴. فیلتر بازه تاریخ برگزاری
    if start_date or end_date:
        date_range = {}
        if start_date:
            date_range["gte"] = start_date
        if end_date:
            date_range["lte"] = end_date
        filter_conditions.append({"range": {"event_date": date_range}})

    # ترکیب شرایط در ساختار bool query
    query_body = {
        "query": {
            "bool": {
                "must": must_conditions if must_conditions else [{"match_all": {}}],
                "filter": filter_conditions
            }
        }
    }

    return query_body