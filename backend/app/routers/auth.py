from fastapi import APIRouter, HTTPException, status
from app.schemas.auth import (
    SendOTPRequest, SendOTPResponse,
    VerifyOTPRequest, VerifyOTPResponse, UserData,
    SignupRequest, SignupResponse,
    LoginRequest, LoginResponse
)
from app.core.redis_client import redis_client
from app.core.config import settings
from app.core.database import execute_query
from app.core.security import create_access_token, hash_password, create_access_token, verify_password
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
        SELECT user_id, first_name, last_name, email, phone, role_id, status 
        FROM users 
        WHERE email = %s OR phone = %s
        LIMIT 1;
    """

    user_row = execute_query(sql_query,params=(identifier, identifier), fetch_one=True)

    # If user record does not exist in DB, signal that registration is required
    if not user_row:
        return VerifyOTPResponse(
            message="OTP verified successfully. User signup is required.",
            is_new_user=True,
            access_token=None,
            user=None
        )

    # Verify if user account is enabled
    if user_row.get("status", "active") == "deactive":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated."
        )

    # Issue JWT token for existing user
    token_payload = {
        "sub": str(user_row["user_id"]),
        "role": user_row["role_id"]
    }
    access_token = create_access_token(token_payload)

    return VerifyOTPResponse(
        message="Login successful.",
        is_new_user=False,
        access_token=access_token,
        token_type="bearer",
        user=UserData(
            user_id=user_row["user_id"],
            first_name=user_row.get("first_name"),
            last_name=user_row.get("last_name"),
            email=user_row.get("email"),
            phone=user_row.get("phone"),
            role_id=user_row["role_id"],
            status=user_row["status"]
        )
    )

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):

    identifier = request.identifier.strip().lower() 
    entered_password = request.password.strip()

    sql_query = """
            SELECT user_id, first_name, last_name, email, phone, role_id, status, password_hash
            FROM users 
            WHERE email = %s OR phone = %s
            LIMIT 1;
        """
    
    user_row = execute_query(sql_query,params=(identifier, identifier), fetch_one=True)

    # If user record does not exist in DB, signal that registration is required
    if not user_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="username isn't exsist."
        )

    if not verify_password(entered_password, user_row['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="password is incorrect"
        )

    # Verify if user account is enabled
    if user_row.get("status", "active") == "deactive":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated."
        )

    # Issue JWT token for existing user
    token_payload = {
        "sub": str(user_row["user_id"]),
        "role": user_row["role_id"]
    }
    access_token = create_access_token(token_payload)

    return LoginResponse(
        message="Login successful.",
        access_token=access_token,
        token_type="bearer",
        user=UserData(
            user_id=user_row["user_id"],
            first_name=user_row.get("first_name"),
            last_name=user_row.get("last_name"),
            email=user_row.get("email"),
            phone=user_row.get("phone"),
            role_id=user_row["role_id"],
            status=user_row["status"]
        )
    )

@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup(request: SignupRequest):
    """
    Complete user registration by hashing password and inserting into PostgreSQL.
    """
    # Ensure at least one identifier is provided
    if not request.email and not request.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either email or phone number must be provided."
        )

    # 1. Check if user already exists in PostgreSQL
    check_query = """
        SELECT user_id FROM users 
        WHERE (email IS NOT NULL AND email = %s) 
           OR (phone IS NOT NULL AND phone = %s)
        LIMIT 1;
    """
    # Using execute_query helper
    existing_user = execute_query(check_query, (request.email, request.phone), fetch_one=True)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or phone already exists."
        )

    # 2. Hash the user password securely
    hashed_pwd = hash_password(request.password)

    # 3. Insert new user into DB using raw SQL
    insert_query = """
        INSERT INTO users (first_name, last_name, email, phone, password_hash, role_id, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING user_id, first_name, last_name, email, phone, role_id, status;
    """
    params = (
        request.first_name,
        request.last_name,
        request.email,
        request.phone,
        hashed_pwd,
        request.role_id,
        "active"
    )
    
    new_user = execute_query(insert_query, params=params, fetch_one=True, commit=True)

    # 4. Issue access JWT token for the newly registered user
    token_payload = {
        "sub": str( new_user["user_id"]),
        "role": new_user["role_id"]
    }
    access_token = create_access_token(token_payload)

    return SignupResponse(
        message="User registered successfully.",
        access_token=access_token,
        token_type="bearer",
        user=UserData(
            user_id=new_user["user_id"],
            first_name=new_user["first_name"],
            last_name=new_user["last_name"],
            email=new_user["email"],
            phone=new_user["phone"],
            role_id=new_user["role_id"],
            status=new_user["status"]
        )
    )