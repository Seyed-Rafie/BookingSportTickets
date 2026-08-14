from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CreateReportRequest(BaseModel):
    report_category_id: int = Field(..., example=1, description="Category ID (1: Payment, 2: Seat, 3: Ticket Fake/Scam)")
    description: str = Field(..., min_length=10, example="Payment was deducted from my account but booking failed.")
    reservation_id: Optional[int] = Field(None, example=1, description="Optional reservation ID")
    ticket_id: Optional[int] = Field(None, example=1, description="Optional ticket ID")

class CreateReportResponse(BaseModel):
    report_id: int
    user_id: int
    ticket_id: Optional[int] = None
    reservation_id: Optional[int] = None
    report_category_id: int
    description: str
    status: str
    submitted_at: datetime