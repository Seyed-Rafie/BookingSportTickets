import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

# فرض بر این است که تابع execute_query در فایل app/db/database.py قرار دارد
# اگر اسم فایل یا پوشه شما فرق دارد، این لاین را متناسب با آن تغییر دهید
from app.core.database import execute_query

router = APIRouter(prefix="/reservations", tags=["Reservations & Payments"])


# ---------------------------------------------------------
# مدل‌های داده ورودی (Pydantic Models)
# ---------------------------------------------------------
class ReservationCreate(BaseModel):
    user_id: int
    ticket_id: int

class PaymentCreate(BaseModel):
    reservation_id: int
    payment_method: str  # برای مثال: 'CARD' یا 'WALLET'


# ---------------------------------------------------------
# APIهای رزرو و پرداخت
# ---------------------------------------------------------

# ۱. API ایجاد رزرو موقت
@router.post("")
def create_reservation(data: ReservationCreate):
    # بررسی موجود بودن بلیط
    ticket = execute_query("SELECT * FROM tickets WHERE id = %s AND status = 'AVAILABLE'", (data.ticket_id,))
    if not ticket:
        raise HTTPException(status_code=400, detail="بلیط موجود نیست یا قبلاً خریده شده است.")

    # ثبت رزرو با ۱۰ دقیقه مهلت پرداخت
    expires_at = datetime.datetime.now() + datetime.timedelta(minutes=10)
    
    insert_query = """
        INSERT INTO reservations (user_id, ticket_id, status, expires_at)
        VALUES (%s, %s, 'PENDING', %s)
        RETURNING id, status, expires_at;
    """
    new_res = execute_query(insert_query, (data.user_id, data.ticket_id, expires_at))
    
    # تغییر وضعیت بلیط به حالت رزرو شده
    execute_query("UPDATE tickets SET status = 'RESERVED' WHERE id = %s", (data.ticket_id,))
    
    return {"message": "رزرو موقت ایجاد شد. ۱۰ دقیقه فرصت پرداخت دارید.", "reservation": new_res[0]}


# ۲. API ثبت و نهایی‌سازی پرداخت
@router.post("")
def create_reservation(data: ReservationCreate):
    try:
        # ۱. بررسی موجود بودن بلیط (استفاده از ticket_id به جای id)
        ticket = execute_query(
            "SELECT * FROM tickets WHERE ticket_id = %s AND status = 'AVAILABLE'", 
            (data.ticket_id,), 
            fetch_one=True
        )
        
        if not ticket:
            raise HTTPException(status_code=404, detail="بلیطی با این مشخصات یا وضعیت پیدا نشد.")

        # ۲. ثبت رزرو موقت
        expires_at = datetime.datetime.now() + datetime.timedelta(minutes=10)
        
        insert_query = """
            INSERT INTO reservations (user_id, ticket_id, status, expires_at)
            VALUES (%s, %s, 'PENDING', %s)
            RETURNING reservation_id, status, expires_at;
        """
        new_res = execute_query(
            insert_query, 
            (data.user_id, data.ticket_id, expires_at), 
            fetch_one=True, 
            commit=True
        )
        
        # ۳. تغییر وضعیت بلیط
        execute_query(
            "UPDATE tickets SET status = 'RESERVED' WHERE ticket_id = %s", 
            (data.ticket_id,), 
            commit=True
        )
        
        return {"message": "رزرو موقت ایجاد شد.", "reservation": new_res}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطای سرور: {str(e)}")


# ۳. API مشاهده تاریخچه خریدهای یک کاربر
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
