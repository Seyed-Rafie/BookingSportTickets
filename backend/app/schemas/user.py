from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserProfileResponse(BaseModel):
    user_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role_id: int
    status: str

class UpdateProfileRequest(BaseModel):
    first_name: Optional[str] = Field(None, example="Ali")
    last_name: Optional[str] = Field(None, example="Rezaei")
    email: Optional[EmailStr] = Field(None, example="ali.new@example.com")
    phone: Optional[str] = Field(None, example="09129998877")