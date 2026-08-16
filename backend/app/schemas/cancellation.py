from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class PenaltyCheckResponseSchema(BaseModel):
    reservation_id: int
    ticket_price: float
    quantity: int
    total_price: float
    hours_until_match: float
    penalty_percent: float
    penalty_amount: float
    refundable_amount: float

class CancellationRequestCreateSchema(BaseModel):
    reservation_id: int
    user_note: Optional[str] = None

class CancellationRequestResponseSchema(BaseModel):
    request_id: int
    reservation_id: int
    status: str
    requested_at: datetime
    message: str

class CancellationRequestSummaryResponse(BaseModel):
    request_id: int
    reservation_id: int
    user_id: int
    request_type: str = Field(..., description="Values: cancel or change_seat")
    status: str = Field(..., description="Values: pending, approved, rejected")
    reviewed_by_support_id: Optional[int] = None
    requested_new_seat_id: Optional[int] = None
    user_note: Optional[str] = None
    admin_note: Optional[str] = None
    requested_at: datetime

class CancellationRequestDetailResponse(BaseModel):
    request_id: int
    reservation_id: int
    user_id: int
    request_type: str = Field(..., description="Values: cancel or change_seat")
    status: str = Field(..., description="Values: pending, approved, rejected")
    reviewed_by_support_id: Optional[int] = None
    requested_new_seat_id: Optional[int] = None
    user_note: Optional[str] = None
    admin_note: Optional[str] = None
    requested_at: datetime
    reservation_status: Optional[str] = Field(None, description="Current status of the associated reservation")

class CancellationRequestReviewInput(BaseModel):
    status: str = Field(..., description="Must be 'approved' or 'rejected'")
    admin_note: Optional[str] = Field(None, description="Explanation or note from admin/support")

    @field_validator('status')
    def validate_status(cls, value):
        allowed_statuses = ['approved', 'rejected']
        if value not in allowed_statuses:
            raise ValueError(f"Status must be one of {allowed_statuses}")
        return value