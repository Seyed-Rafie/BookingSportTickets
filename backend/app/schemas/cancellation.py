from pydantic import BaseModel
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