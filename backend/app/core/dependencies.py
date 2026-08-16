from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from app.core.config import settings
from app.core.database import execute_query

# Configure Http bearer scheme for Swagger UI
security_scheme = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> dict:
    """
    Extract and validate JWT token from header, then fetch user record from DB.
    """

    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode signed JWT token0=
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except Exception:
        raise credentials_exception

    # Query user from PostgreSQL using custom schema columns
    query = """
        SELECT user_id, first_name, last_name, email, phone, role_id, status
        FROM users
        WHERE user_id = %s
        LIMIT 1;
    """
    user = execute_query(query, (user_id,), fetch_one=True)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    # Check status against string value 'active'
    if user.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactive."
        )

    return user

def get_current_support_user(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Ensure current authenticated user has Admin (1) or Support (3) role.
    """
    allowed_roles = [1, 3]  # 1: Admin, 3: Support
    if current_user.get("role_id") not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Support or Admin privileges required."
        )
    return current_user

def get_current_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Ensure current authenticated user has Admin (1)
    """
    allowed_roles = [1]  # 1: Admin
    if current_user.get("role_id") not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Support or Admin privileges required."
        )
    return current_user