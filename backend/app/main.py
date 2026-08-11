from fastapi import FastAPI, HTTPException, status
from app.core.database import check_db_health
from app.core.redis_client import check_redis_health
from app.routers.auth import router as auth_router

app = FastAPI(
    title="Sports Ticketing System API",
    description="booking sport ticket platform",
    version="1.0.0"
)

app.include_router(auth_router)

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
    redis_healthy = check_redis_healthy = check_redis_health()

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