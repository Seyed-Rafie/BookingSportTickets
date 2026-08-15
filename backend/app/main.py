from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware  # ۱. اضافه شدن اینپورت CORS

from app.core.database import check_db_health
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
# ۲. تنظیمات CORS Middleware برای اجازه به مرورگر (Preflight / OPTIONS)
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # در محیط توسعه به تمام Originها اجازه داده می‌شود
    allow_credentials=True,
    allow_methods=["*"],  # اجازه به تمامی متدها (POST, GET, OPTIONS, PUT, DELETE)
    allow_headers=["*"],  # اجازه به تمامی هدرها (Content-Type, Authorization, ...)
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
# Endpoint‌های عمومی پروژه
# ------------------------------------------------------------
@app.get("/", tags=["Root"])
def read_root():
    return {
        "message": "Welcome to Sports Ticketing System API!",
        "docs_url": "/docs"
    }


@app.get("/health", tags=["Health Check"])
def health_check():
    # بررسی سلامت دیتابیس و ردیس
    db_healthy = check_db_health()
    redis_healthy = check_redis_health()
    es_health = check_es_health()

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