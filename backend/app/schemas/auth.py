from pydantic import BaseModel, Field
from typing import Optional

class SendOTPRequest(BaseModel):
    # Input identifier can be phone number or email string
    identifier: str = Field(..., description="User email or phone number", example="09121112233")

class VerifyOTPRequest(BaseModel):
    identifier: str = Field(..., description="User email or phone number", example="09121112233")
    code: str = Field(..., min_length=4, max_length=6, description="OTP code received", example="123456")

class SendOTPResponse(BaseModel):
    message: str
    expires_in: int

class UserData(BaseModel):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str
    status: str

class VerifyOTPResponse(BaseModel):
    message: str
    is_new_user: bool
    access_token: Optional[str] = None
    token_type: Optional[str] = "bearer"
    user: Optional[UserData] = None