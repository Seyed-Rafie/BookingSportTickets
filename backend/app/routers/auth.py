from fastapi import APIRouter, HTTPException, status
from app.schemas.auth import (
    SendOTPRequest, SendOTPResponse,
    VerifyOTPRequest, VerifyOTPResponse, UserData
)
from app.core.redis_client import redis_client
from app.core.config import settings
from app.core.database import execute_query
from app.core.security import create_access_token
from app.utils.otp import generate_otp_code, send_otp_notification

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/send-otp", response_model=SendOTPResponse)
def send_otp(request: SendOTPRequest):
    """
    Step 1: Generate OTP, store in Redis with TTL, and dispatch to user.
    """
    identifier = request.identifier.strip()

    # Rate limiting: Prevent spam if OTP code was requested less than 30s ago
    existing_ttl = redis_client.ttl(f"otp:{identifier}")
    if existing_ttl > (settings.OTP_EXPIRE_SECONDS - 30):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Please wait before requesting a new code."
        )

    # Generate random 6-digit OTP code
    otp_code = generate_otp_code(length=settings.OTP_LENGTH)

    # Store OTP in Redis with 120s expiration TTL
    redis_client.setex(
        name=f"otp:{identifier}",
        time=settings.OTP_EXPIRE_SECONDS,
        value=otp_code
    )

    # Send OTP code (Console output / SMS Service)
    send_otp_notification(identifier, otp_code)

    return SendOTPResponse(
        message="OTP code generated and sent successfully.",
        expires_in=settings.OTP_EXPIRE_SECONDS
    )


@router.post("/verify-otp", response_model=VerifyOTPResponse)
def verify_otp(request: VerifyOTPRequest):
    """
    Step 2: Verify submitted OTP against Redis. Check DB for user record and emit JWT token.
    """
    identifier = request.identifier.strip()
    submitted_code = request.code.strip()

    # Retrieve stored OTP code from Redis key
    cached_code = redis_client.get(f"otp:{identifier}")

    # Check if OTP key exists and matches
    if not cached_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP code has expired or was not requested."
        )

    if cached_code != submitted_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code."
        )

    # Delete used OTP code from Redis immediately after validation
    redis_client.delete(f"otp:{identifier}")

    # Raw SQL Query to check existing user in PostgreSQL (NO ORM used)
    sql_query = """
        SELECT id, name, email, phone, role, is_active 
        FROM users 
        WHERE email = %s OR phone = %s
        LIMIT 1;
    """

    user_row = execute_query(sql_query,(identifier, identifier), True)

    # If user record does not exist in DB, signal that registration is required
    if not user_row:
        return VerifyOTPResponse(
            message="OTP verified successfully. User signup is required.",
            is_new_user=True,
            access_token=None,
            user=None
        )

    # Verify if user account is enabled
    if not user_row.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated."
        )

    # Issue JWT token for existing user
    token_payload = {
        "sub": str(user_row["id"]),
        "role": user_row["role"]
    }
    access_token = create_access_token(token_payload)

    return VerifyOTPResponse(
        message="Login successful.",
        is_new_user=False,
        access_token=access_token,
        token_type="bearer",
        user=UserData(
            id=user_row["id"],
            name=user_row.get("name"),
            email=user_row.get("email"),
            phone=user_row.get("phone"),
            role=user_row["role"],
            is_active=user_row["is_active"]
        )
    )