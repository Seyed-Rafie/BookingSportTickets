import logging
from typing import Optional, Dict, Any
from elasticsearch import AsyncElasticsearch, NotFoundError
from app.core.config import settings

# ۱. دریافت آدرس کامل Bonsai از فایل .env
ELASTICSEARCH_URL = settings.ELASTICSEARCH_URL

# ۲. ساخت کلاینت ناهمگام
es_client = AsyncElasticsearch(ELASTICSEARCH_URL)

TICKETS_INDEX = "tickets"

logger = logging.getLogger(__name__)

# نگاشت بهینه‌شده با آنالایزر فارسی برای جستجوی دقیق‌تر
TICKETS_INDEX_MAPPING = {
    "settings": {
        "analysis": {
            "analyzer": {
                "persian_analyzer": {
                    "tokenizer": "standard",
                    "filter": ["lowercase", "persian_normalization"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            # فیلدهای عددی و شناسه
            "ticket_id": {"type": "long"},
            "ticket_code": {"type": "keyword"},
            "match_id": {"type": "long"},
            "category_id": {"type": "integer"},
            "total_capacity": {"type": "integer"},
            "remaining_capacity": {"type": "integer"},
            "price": {"type": "double"},
            "ticket_status": {"type": "keyword"},
            
            # فیلدهای متنی همراه با آنالایزر فارسی
            "title": {"type": "text", "analyzer": "persian_analyzer"},
            "home_team": {"type": "text", "analyzer": "persian_analyzer"},
            "away_team": {"type": "text", "analyzer": "persian_analyzer"},
            "venue_name": {"type": "text", "analyzer": "persian_analyzer"},
            
            # فیلدهای دقیق (Keyword)
            "sport_type": {"type": "keyword"},
            "city": {"type": "keyword"},
            "category_name": {"type": "keyword"},
            "event_date": {"type": "date"},
            "match_status": {"type": "keyword"}
        }
    }
}


async def get_es_client() -> AsyncElasticsearch:
    """تأمین کلاینت برای FastAPI Dependency Injection"""
    return es_client


async def close_es_client() -> None:
    """بستن اتصال الاستیک‌سرچ هنگام Shutdown سرور"""
    await es_client.close()


async def check_es_health() -> bool:
    """بررسی سلامت اتصال به Elasticsearch"""
    try:
        is_alive = await es_client.ping()
        if is_alive:
            return True
        logger.error("Error in connecting to ElasticSearch: Ping failed")
        return False
    except Exception as e:
        logger.error(f"ElasticSearch Health Check Exception: {e}")
        return False


async def init_es_index() -> None:
    """ایجاد ایندکس در صورت عدم وجود هنگام راه‌اندازی سرور"""
    try:
        exists = await es_client.indices.exists(index=TICKETS_INDEX)
        if not exists:
            await es_client.indices.create(
                index=TICKETS_INDEX,
                mappings=TICKETS_INDEX_MAPPING["mappings"],
                settings=TICKETS_INDEX_MAPPING["settings"]
            )
            logger.info(f"[Elasticsearch] Index '{TICKETS_INDEX}' created successfully.")
    except Exception as e:
        logger.error(f"[Elasticsearch Error] Failed to initialize index: {e}")


def build_ticket_search_query(
    q: Optional[str] = None,
    sport_type: Optional[str] = None,
    city: Optional[str] = None,
    category_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """ساخت کوئری هوشمند Elastic DSL جهت فیلتر و جستجوی بلیط‌ها"""
    must_conditions = []
    
    # شرایط پایه: فقط بلیط‌های فعال و دارای ظرفیت نمایش داده شوند
    filter_conditions = [
        {"term": {"ticket_status": "active"}},
        {"range": {"remaining_capacity": {"gt": 0}}}
    ]

    # ۱. جستجوی متنی
    if q and q.strip():
        must_conditions.append({
            "multi_match": {
                "query": q.strip(),
                "fields": ["title^3", "home_team^2", "away_team^2", "venue_name"],
                "fuzziness": "AUTO"
            }
        })

    # ۲. فیلترهای Exact Match
    if sport_type and sport_type.strip():
        filter_conditions.append({"term": {"sport_type": sport_type.strip()}})

    if city and city.strip():
        filter_conditions.append({"term": {"city": city.strip()}})

    if category_id is not None:
        filter_conditions.append({"term": {"category_id": category_id}})

    # ۳. فیلتر قیمت
    if min_price is not None or max_price is not None:
        price_range = {}
        if min_price is not None:
            price_range["gte"] = min_price
        if max_price is not None:
            price_range["lte"] = max_price
        filter_conditions.append({"range": {"price": price_range}})

    # ۴. فیلتر تاریخ مسابقه
    if start_date or end_date:
        date_range = {}
        if start_date and start_date.strip():
            date_range["gte"] = start_date.strip()
        if end_date and end_date.strip():
            date_range["lte"] = end_date.strip()
        filter_conditions.append({"range": {"event_date": date_range}})

    return {
        "query": {
            "bool": {
                "must": must_conditions if must_conditions else [{"match_all": {}}],
                "filter": filter_conditions
            }
        }
    }


async def index_ticket_doc(ticket_doc: Dict[str, Any]) -> None:
    """ذخیره یا بروزرسانی یک بلیط در Elastic"""
    ticket_id = ticket_doc.get("ticket_id")
    if not ticket_id:
        raise ValueError("ticket_doc must contain a 'ticket_id'")
        
    await es_client.index(
        index=TICKETS_INDEX,
        id=str(ticket_id),
        document=ticket_doc
    )


async def delete_ticket_doc(ticket_id: int) -> None:
    """حذف سند بلیط از Elastic"""
    try:
        await es_client.delete(
            index=TICKETS_INDEX,
            id=str(ticket_id)
        )
    except NotFoundError:
        pass  # سند در الاستیک‌سرچ وجود نداشته و نیازی به کرش نیست