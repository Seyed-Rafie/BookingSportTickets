from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.user import UserProfileResponse, UpdateProfileRequest
from app.core.dependencies import get_current_user
from app.core.database import execute_query
from app.core.redis_client import redis_client

router = APIRouter(prefix="/users", tags=["Users Profile"])

@router.get("/me", response_model=UserProfileResponse)
def get_my_profile(current_user: dict = Depends(get_current_user)):
    """
    Retrieve current authenticated user profile data.
    """
    return current_user


@router.patch("/me", response_model=UserProfileResponse)
def update_my_profile(
    request: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update profile details for current authenticated user and invalidate cache.
    """
    user_id = current_user["user_id"]

    # Dynamically prepare SQL fields and query parameters
    update_fields = []
    params = []

    if request.first_name is not None:
        update_fields.append("first_name = %s")
        params.append(request.first_name)

    if request.last_name is not None:
        update_fields.append("last_name = %s")
        params.append(request.last_name)

    if request.email is not None:
        update_fields.append("email = %s")
        params.append(request.email)

    if request.phone is not None:
        update_fields.append("phone = %s")
        params.append(request.phone)

    # If no fields provided in payload, return error
    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided to update."
        )

    # Append user_id for WHERE clause condition
    params.append(user_id)

    # Build dynamic UPDATE SQL query
    query = f"""
        UPDATE users
        SET {', '.join(update_fields)}
        WHERE user_id = %s
        RETURNING user_id, first_name, last_name, email, phone, role_id, status;
    """

    # Execute update query with commit=True as required for mutations
    updated_user = execute_query(query, tuple(params), commit=True, fetch_one=True)

    # Invalidate cached user profile in Redis if present
    redis_client.delete(f"user_profile:{user_id}")

    return updated_user