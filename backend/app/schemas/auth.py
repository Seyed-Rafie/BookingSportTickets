from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class SendOTPRequest(BaseModel):
    # Input identifier can be phone number or email string
    identifier: str = Field(..., description="User email or phone number", example="09120000001 or abc@example.com")

class VerifyOTPRequest(BaseModel):
    identifier: str = Field(..., description="User email or phone number", example="09120000001 or abc@example.com")
    code: str = Field(..., min_length=4, max_length=6, description="OTP code received", example="123456")

class SendOTPResponse(BaseModel):
    message: str
    expires_in: int

class UserData(BaseModel):
    user_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role_id: int
    status: str

class VerifyOTPResponse(BaseModel):
    message: str
    is_new_user: bool
    access_token: Optional[str] = None
    token_type: Optional[str] = "bearer"
    user: Optional[UserData] = None

class SignupRequest(BaseModel):
    first_name: str = Field(..., min_length=2, example="Ali")
    last_name: str = Field(..., min_length=2, example="Rezaei")
    email: Optional[EmailStr] = Field(None, example="ali@example.com")
    phone: Optional[str] = Field(None, example="09121112233")
    password: str = Field(..., min_length=6, example="SecretPassword123")
    role_id: int = Field("2", example="1")  # Default role is Customer; 1:Admin, 2:Customer, 3:Support

class SignupResponse(BaseModel):
    message: str
    access_token: str
    token_type: str = "bearer"
    user: UserData