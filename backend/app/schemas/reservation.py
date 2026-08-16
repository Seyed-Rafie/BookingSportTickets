from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


# ==========================================
# ۱. مدل‌های API شماره ۷: رزرو موقت (POST /reservations)
# ==========================================
class ReservationCreate(BaseModel):
    ticket_id: int = Field(..., description="شناسه بلیط مسابقه")
    seat_ids: List[int] = Field(..., min_length=1, description="لیست شناسه‌های صندلی انتخابی")


class ReservationResponse(BaseModel):
    reservation_id: int
    user_id: int
    ticket_id: int
    quantity: int
    status: str
    total_price: Decimal
    reserved_at: datetime
    reserved_until: datetime
    seat_ids: List[int]


# ==========================================
# ۲. مدل‌های API شماره ۸: درخواست OTP و ثبت پرداخت (POST /reservations/payments)
# ==========================================
class PaymentOtpRequest(BaseModel):
    reservation_id: int = Field(..., description="شناسه رزرو")
    card_number: str = Field(..., min_length=16, max_length=16, description="شماره کارت ۱۶ رقمی")


class PaymentCreate(BaseModel):
    reservation_id: int = Field(..., description="شناسه رزرو")
    method: str = Field("bank_card", example="bank_card", description="روش پرداخت: bank_card, online, wallet, fake")
    card_number: str = Field(..., max_length=16, description="شماره کارت")
    expiry_month: str = Field(..., max_length=2, description="ماه انقضا")
    expiry_year: str = Field(..., max_length=2, description="سال انقضا")
    cvv2: str = Field(..., max_length=4, description="کد CVV2")
    otp_code: str = Field(..., max_length=6, description="رمز پویا")


class PaymentResponse(BaseModel):
    payment_id: int
    reservation_id: int
    amount: Decimal
    method: str
    status: str
    paid_at: datetime
    transaction_code: str


# ==========================================
# ۳. مدل‌های API شماره ۱۱: تاریخچه خرید کاربر (GET /reservations/me)
# ==========================================
class ReservationSeatDetail(BaseModel):
    seat_id: int
    section: Optional[str]
    row: Optional[str]
    seat_number: Optional[str]


class UserReservationHistory(BaseModel):
    reservation_id: int
    match_title: str
    venue_name: str
    match_datetime: datetime
    total_price: Decimal
    status: str
    reserved_at: datetime
    reserved_until: datetime
    seats: List[ReservationSeatDetail]