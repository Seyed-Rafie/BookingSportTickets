import logging
from typing import Optional, Dict, Any
from elasticsearch import AsyncElasticsearch, NotFoundError
from app.core.config import settings
from app.core.database import execute_query

# ۱. دریافت آدرس کامل Bonsai از فایل .env
ELASTICSEARCH_URL = settings.ELASTICSEARCH_URL

# ۲. ساخت کلاینت ناهمگام
es_client = AsyncElasticsearch(ELASTICSEARCH_URL)

TICKETS_INDEX = "tickets"

logger = logging.getLogger(__name__)

# نگاشت بهینه‌شده با آنالایزر فارسی برای جستجوی دقیق‌تر
TICKETS_INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "ticket_id": {"type": "long"},
            "ticket_code": {"type": "keyword"},
            "match_id": {"type": "long"},
            "category_id": {"type": "integer"},
            "sport_type_id": {"type": "integer"},
            "city_id": {"type": "integer"},
            "home_team_id": {"type": "integer"},
            "away_team_id": {"type": "integer"},
            "total_capacity": {"type": "integer"},
            "remaining_capacity": {"type": "integer"},
            "price": {"type": "double"},
            "ticket_status": {"type": "keyword"},
            
            "title": {"type": "text", "analyzer": "standard"},
            "home_team": {"type": "text"},
            "away_team": {"type": "text"},
            "sport_type": {"type": "keyword"},
            "venue_name": {"type": "text"},
            "city": {"type": "keyword"},
            "category_name": {"type": "keyword"},
            "competition_name": {"type": "keyword"},
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
    """ایجاد ایندکس در صورت عدم وجود (با رفع خطاهای خاموش)"""
    try:
        exists = await es_client.indices.exists(index=TICKETS_INDEX)
        if not exists:
            response = await es_client.indices.create(
                index=TICKETS_INDEX,
                body=TICKETS_INDEX_MAPPING
            )
            print(f"[Elasticsearch] Index '{TICKETS_INDEX}' created: {response}")
        else:
            print(f"[Elasticsearch] Index '{TICKETS_INDEX}' already exists.")
    except Exception as e:
        print(f"[Elasticsearch Critical Error] Failed to create index: {e}")
        raise e  # انتشار خطا جهت متوقف ساختن اسکریپت در صورت عدم ساخت ایندکس

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
        body=ticket_doc
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

async def fetch_enriched_ticket(ticket_id: int) -> Optional[Dict[str, Any]]:
    """استخراج داده جامع بلیط همراه با جزئیات ورزشی و جداول پایه طبق ERD"""
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
            tc.name AS category_name,
            st.name AS sport_type,
            ci.name AS city,
            ht.name AS home_team,
            at.name AS away_team,
            comp.name AS competition_name,
            CONCAT(COALESCE(ht.name, ''), ' - ', COALESCE(at.name, '')) AS title,
            -- Football Details
            fd.gate_number AS fb_gate_number,
            fd.has_parking AS fb_has_parking,
            fd.vip_services AS fb_vip_services,
            -- Basketball Details
            bd.entrance_gate AS bb_entrance_gate,
            bd.vip_services AS bb_vip_services,
            bd.has_food_court AS bb_has_food_court,
            -- Volleyball Details
            vd.entrance_gate AS vb_entrance_gate,
            vd.special_services AS vb_special_services
        FROM TICKETS t
        JOIN MATCHES m ON t.match_id = m.match_id
        JOIN VENUES v ON m.venue_id = v.venue_id
        JOIN TICKET_CATEGORIES tc ON t.category_id = tc.category_id
        LEFT JOIN TEAMS ht ON m.home_team_id = ht.team_id
        LEFT JOIN TEAMS at ON m.away_team_id = at.team_id
        LEFT JOIN SPORT_TYPES st ON m.sport_type_id = st.sport_type_id
        LEFT JOIN CITIES ci ON v.city_id = ci.city_id
        LEFT JOIN COMPETITIONS comp ON m.competition_id = comp.competition_id
        LEFT JOIN FOOTBALL_DETAILS fd ON t.ticket_id = fd.ticket_id
        LEFT JOIN BASKETBALL_DETAILS bd ON t.ticket_id = bd.ticket_id
        LEFT JOIN VOLLEYBALL_DETAILS vd ON t.ticket_id = vd.ticket_id
        WHERE t.ticket_id = %s;
    """
    records = execute_query(query, (ticket_id,), fetch_all=True)
    return records[0] if records else None

async def sync_ticket_to_es(ticket_id: int) -> None:
    """خواندن داده جدید از PostgreSQL و ارسال Upsert به Elastic"""
    try:
        record = await fetch_enriched_ticket(ticket_id)
        if not record:
            await delete_ticket_doc(ticket_id)
            return

        doc = {
            "ticket_id": record["ticket_id"],
            "ticket_code": record["ticket_code"],
            "match_id": record["match_id"],
            "category_id": record["category_id"],
            "sport_type_id": record["sport_type_id"],
            "city_id": record["city_id"],
            "home_team_id": record["home_team_id"] or 0,
            "away_team_id": record["away_team_id"] or 0,
            "total_capacity": record["total_capacity"],
            "remaining_capacity": record["remaining_capacity"],
            "price": float(record["price"]),
            "ticket_status": record["ticket_status"],
            "title": record["title"],
            "home_team": record["home_team"] or "",
            "away_team": record["away_team"] or "",
            "sport_type": record["sport_type"] or "",
            "venue_name": record["venue_name"] or "",
            "city": record["city"] or "",
            "category_name": record["category_name"] or "",
            "competition_name": record["competition_name"] or "",
            "event_date": record["event_date"].isoformat() if record.get("event_date") else None,
            "match_status": record["match_status"] or "",
            # ساختار جزئیات ورزشی درون سند Elastic
            "details": {
                "gate_number": record.get("fb_gate_number") or record.get("bb_entrance_gate") or record.get("vb_entrance_gate"),
                "has_parking": record.get("fb_has_parking"),
                "has_food_court": record.get("bb_has_food_court"),
                "vip_services": record.get("fb_vip_services") or record.get("bb_vip_services") or record.get("vb_special_services")
            }
        }
        await index_ticket_doc(doc)
    except Exception as e:
        logger.error(f"خطا در همگام‌سازی بلیط {ticket_id} با Elasticsearch: {e}")