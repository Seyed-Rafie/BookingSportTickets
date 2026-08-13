from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ReportResponseUpdate(BaseModel):
    admin_response: str = Field(..., min_length=3, example="Refund processed and issue investigated.")
    status: str = Field(..., example="resolved", description="Options: resolved, rejected, under_review")

class ReservationStatusUpdate(BaseModel):
    status: str = Field(..., example="cancelled", description="Allowed: reserved, paid, cancelled, expired")

class AdminReportResponse(BaseModel):
    report_id: int
    user_id: int
    ticket_id: Optional[int] = None
    reservation_id: Optional[int] = None
    report_category_id: int
    description: str
    status: str
    reviewed_by_support_id: Optional[int] = None
    admin_response: Optional[str] = None
    submitted_at: datetime