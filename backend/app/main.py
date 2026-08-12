from fastapi import FastAPI, HTTPException, status
from app.core.database import check_db_health
from app.core.redis_client import check_redis_health
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers import reservations  # ۱. این خط را برای اضافه کردن روتر خودت اضافه کن

app = FastAPI(
    title="Sports Ticketing System API",
    description="booking sport ticket platform",
    version="1.0.0"
)

app.include_router(auth_router)
app.include_router(users_router)

# ۲. این خط را اضافه کن تا APIهای رزرو و پرداخت به برنامه متصل شوند
app.include_router(reservations.router)

@app.get("/", tags=["Root"])
def read_root():
    # welcome message and redirect to Swagger
    return {
        "message": "welcome!",
        "docs_url": "/docs"
    }

@app.get("/health", tags=["Health Check"])
def health_check():
    # checking health of database and redis
    db_healthy = check_db_health()
    redis_healthy = check_redis_health() # اصلاح یک اشتباه تایپی کوچک در کد قبلی شما

    is_all_healthy = db_healthy and redis_healthy

    status_code = status.HTTP_200_OK if is_all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    response_payload = {
        "status": "healthy" if is_all_healthy else "unhealthy",
        "services": {
            "postgres_neon": "connected" if db_healthy else "disconnected",
            "redis_cache": "connected" if redis_healthy else "disconnected"
        }
    }

    if not is_all_healthy:
        raise HTTPException(
            status_code=status_code,
            detail=response_payload
        )

    return response_payload
