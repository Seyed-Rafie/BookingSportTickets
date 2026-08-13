from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


# ==========================================
# ۱. مدل‌های API شماره ۷: رزرو موقت (POST /reservations)
# ==========================================
class ReservationCreate(BaseModel):
    # دقت کنید: user_id اینجا نیست! از توکن JWT خوانده خواهد شد.
    ticket_ids: List[int] = Field(
        ..., 
        min_length=1, 
        description="لیست شناسه بلیط‌های درخواستی برای رزرو موقت"
    )

class TicketSummary(BaseModel):
    ticket_id: int
    price: Decimal

class ReservationResponse(BaseModel):
    reservation_id: int
    user_id: int
    total_amount: Decimal
    status: str
    expires_at: datetime
    created_at: datetime
    tickets: List[TicketSummary]


# ==========================================
# ۲. مدل‌های API شماره ۸: ثبت پرداخت (POST /payments)
# ==========================================
class PaymentCreate(BaseModel):
    reservation_id: int = Field(..., description="شناسه رزروی که قرار است پرداخت شود")
    payment_method: str = Field(
        ..., 
        example="CARD", 
        description="روش پرداخت (مثلاً: CARD، WALLET)"
    )

class PaymentResponse(BaseModel):
    payment_id: int
    reservation_id: int
    amount: Decimal
    payment_method: str
    transaction_ref: str
    status: str
    created_at: datetime


# ==========================================
# ۳. مدل‌های API شماره ۱۱: تاریخچه خرید کاربر (GET /reservations/me)
# ==========================================
class ReservationItemDetail(BaseModel):
    ticket_id: int
    price: Decimal
    event_title: str
    venue_name: str
    event_date: datetime
    section_name: str
    row_number: str
    seat_number: str

class UserReservationHistory(BaseModel):
    reservation_id: int
    total_amount: Decimal
    status: str
    expires_at: datetime
    created_at: datetime
    items: List[ReservationItemDetail]
