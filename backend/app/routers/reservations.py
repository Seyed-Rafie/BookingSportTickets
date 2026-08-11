from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import datetime
# فرض بر این است که تابع execute_query در فایل db/database.py قرار دارد
from app.db.database import execute_query 

router = APIRouter(prefix="/reservations", tags=["Reservations & Payments"])

class ReservationCreate(BaseModel):
    user_id: int
    ticket_id: int

@router.post("")
def create_reservation(data: ReservationCreate):
    # ۱. بررسی موجود بودن بلیط
    ticket = execute_query("SELECT * FROM tickets WHERE id = %s AND status = 'AVAILABLE'", (data.ticket_id,))
    if not ticket:
        raise HTTPException(status_code=400, detail="بلیط موجود نیست یا قبلاً خریده شده است.")

    # ۲. ثبت رزرو با ۱۰ دقیقه مهلت پرداخت
    expires_at = datetime.datetime.now() + datetime.timedelta(minutes=10)
    
    insert_query = """
        INSERT INTO reservations (user_id, ticket_id, status, expires_at)
        VALUES (%s, %s, 'PENDING', %s)
        RETURNING id, status, expires_at;
    """
    new_res = execute_query(insert_query, (data.user_id, data.ticket_id, expires_at))
    
    # ۳. تغییر وضعیت بلیط به حالت رزرو شده
    execute_query("UPDATE tickets SET status = 'RESERVED' WHERE id = %s", (data.ticket_id,))
    
    return {"message": "رزرو موقت ایجاد شد. ۱۰ دقیقه فرصت پرداخت دارید.", "reservation": new_res[0]}

class PaymentCreate(BaseModel):
    reservation_id: int
    payment_method: str  # مثلا 'CARD' یا 'WALLET'

@router.post("/pay")
def process_payment(data: PaymentCreate):
    # ۱. پیدا کردن رزرو
    res = execute_query("SELECT * FROM reservations WHERE id = %s AND status = 'PENDING'", (data.reservation_id,))
    if not res:
        raise HTTPException(status_code=404, detail="رزرو معتبری یافت نشد یا زمان آن به پایان رسیده است.")

    # ۲. ثبت موفقیت‌آمیز پرداخت
    execute_query("INSERT INTO payments (reservation_id, method, status) VALUES (%s, %s, 'SUCCESS')", (data.reservation_id, data.payment_method))
    
    # ۳. آپدیت وضعیت رزرو و بلیط به PAID و SOLD
    execute_query("UPDATE reservations SET status = 'CONFIRMED' WHERE id = %s", (data.reservation_id,))
    execute_query("UPDATE tickets SET status = 'SOLD' WHERE id = %s", (res[0]['ticket_id'],))

    return {"status": "SUCCESS", "message": "پرداخت با موفقیت انجام شد و بلیط صادر گردید."}

@router.get("/user/{user_id}")
def get_user_reservations(user_id: int):
    query = """
        SELECT r.id as reservation_id, r.status, r.created_at, t.title, t.price, t.event_date
        FROM reservations r
        JOIN tickets t ON r.ticket_id = t.id
        WHERE r.user_id = %s
        ORDER BY r.created_at DESC;
    """
    history = execute_query(query, (user_id,))
    return {"user_id": user_id, "history": history}
