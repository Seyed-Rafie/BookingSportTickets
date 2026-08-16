# In the name of GOD
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from app.core.database import check_db_health, get_db_connection
from app.core.redis_client import check_redis_health
from app.core.elasticsearch import check_es_health

# ایمپورت تمامی روترهای پروژه
from app.routers import (
    venues,
    tickets,
    cancellations,
)

from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.reports import router as reports_router
from app.routers.admin import router as admin_router
from app.routers import reservations

app = FastAPI(
    title="Sports Ticketing System API",
    description="Booking sports tickets platform API with FastAPI, PostgreSQL, and Redis",
    version="1.0.0"
)

# ------------------------------------------------------------
# تنظیمات CORS Middleware
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# ثبت (Register) تمامی روترهای اعضای تیم
# ------------------------------------------------------------
app.include_router(venues.router)
app.include_router(tickets.router)
app.include_router(cancellations.router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(reports_router)
app.include_router(admin_router)
app.include_router(reservations.router)


# ------------------------------------------------------------
# وظیفه پس‌زمینه (Background Job): پاک‌سازی رزروهای منقضی شده
# ------------------------------------------------------------
def cleanup_expired_reservations():
    """این تابع هر چند دقیقه یک‌بار اجرا شده و رزروهای موقت بیش از ۱۰ دقیقه را منقضی می‌کند."""
    print("[Scheduler] Running cleanup task for expired reservations...")
    with get_db_connection() as conn:
        # استفاده از کرسر معمولی چون فقط آپدیت انجام می‌دهیم
        cursor = conn.cursor()
        try:
            # ۱. پیدا کردن رزروهایی که هنوز reserved هستند اما زمانشان گذشته
            cursor.execute(
                """
                SELECT reservation_id, ticket_id, quantity 
                FROM RESERVATIONS 
                WHERE status = 'reserved' AND reserved_until < NOW();
                """
            )
            expired_reservations = cursor.fetchall()

            for res in expired_reservations:
                res_id = res[0]
                ticket_id = res[1]
                quantity = res[2]

                # ۲. آپدیت وضعیت رزرو به expired
                cursor.execute("UPDATE RESERVATIONS SET status = 'expired' WHERE reservation_id = %s;", (res_id,))
                
                # ۳. آزاد کردن صندلی‌ها در RESERVED_SEATS
                cursor.execute("UPDATE RESERVED_SEATS SET status = 'released' WHERE reservation_id = %s;", (res_id,))
                
                # ۴. آزاد کردن وضعیت صندلی‌ها در SEATS
                cursor.execute(
                    """
                    UPDATE SEATS SET status = 'available'
                    WHERE seat_id IN (SELECT seat_id FROM RESERVED_SEATS WHERE reservation_id = %s);
                    """,
                    (res_id,)
                )
                
                # ۵. برگرداندن ظرفیت به بلیط
                cursor.execute(
                    "UPDATE TICKETS SET remaining_capacity = remaining_capacity + %s WHERE ticket_id = %s;",
                    (quantity, ticket_id)
                )

            conn.commit()
            if expired_reservations:
                print(f"[Scheduler] Successfully expired and freed {len(expired_reservations)} reservations.")
                
        except Exception as e:
            conn.rollback()
            print(f"[Scheduler] Error in cleanup task: {e}")
        finally:
            cursor.close()

# ساخت نمونه از زمان‌بند
scheduler = BackgroundScheduler()
# تعریف اجرای تابع هر ۱ دقیقه (می‌توانید به 2 یا 3 دقیقه هم تغییر دهید)
scheduler.add_job(cleanup_expired_reservations, 'interval', minutes=1)

# رویدادهای چرخه حیات اپلیکیشن (Startup / Shutdown)
@app.on_event("startup")
def startup_event():
    # هنگام روشن شدن سرور، زمان‌بند را استارت می‌زنیم
    scheduler.start()
    print("[System] APScheduler started successfully.")

@app.on_event("shutdown")
def shutdown_event():
    # هنگام خاموش شدن سرور، زمان‌بند را متوقف می‌کنیم
    scheduler.shutdown()
    print("[System] APScheduler shut down.")


# ------------------------------------------------------------
# Endpoint‌های عمومی پروژه
# ------------------------------------------------------------
@app.get("/", tags=["Root"])
def read_root():
    return {
        "message": "Welcome to Sports Ticketing System API!",
        "docs_url": "/docs"
    }


@app.get("/health", tags=["Health Check"])
async def health_check():
    # بررسی سلامت دیتابیس و ردیس
    db_healthy = check_db_health()
    redis_healthy = check_redis_health()
    es_health = await check_es_health()

    is_all_healthy = db_healthy and redis_healthy and es_health

    status_code = (
        status.HTTP_200_OK
        if is_all_healthy
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    response_payload = {
        "status": "healthy" if is_all_healthy else "unhealthy",
        "services": {
            "postgres_neon": "connected" if db_healthy else "disconnected",
            "redis_cache": "connected" if redis_healthy else "disconnected",
            "elasticsearch": "connected" if es_health else "disconnected"
        }
    }

    if not is_all_healthy:
        raise HTTPException(
            status_code=status_code,
            detail=response_payload
        )

    return response_payload