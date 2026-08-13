from datetime import datetime, timedelta
from decimal import Decimal
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import get_db_connection
from app.core.dependencies import get_current_user
from app.schemas.reservation import (
    ReservationCreate,
    ReservationResponse,
    TicketSummary,
    PaymentCreate,
    PaymentResponse,
    UserReservationHistory,
    ReservationItemDetail,
)

router = APIRouter(prefix="/reservations", tags=["Reservations & Payments"])


# =========================================================================
# API شماره ۷: ثبت رزرو موقت با مهلت ۱۰ دقیقه (POST /reservations)
# =========================================================================
@router.post("", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
def create_reservation(
    payload: ReservationCreate,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    ticket_ids = payload.ticket_ids

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # ۱. بررسی وجود و آماده‌به‌فروش بودن تمامی بلیط‌های درخواستی
        cursor.execute(
            """
            SELECT ticket_id, price, status 
            FROM tickets 
            WHERE ticket_id = ANY(%s)
            FOR UPDATE;
            """,
            (ticket_ids,)
        )
        fetched_tickets = cursor.fetchall()

        if len(fetched_tickets) != len(set(ticket_ids)):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="یک یا چند بلیط درخواستی یافت نشدند."
            )

        total_amount = Decimal("0.00")
        tickets_summary: List[TicketSummary] = []

        for ticket in fetched_tickets:
            t_id, price, status_val = ticket["ticket_id"], ticket["price"], ticket["status"]
            if status_val != "AVAILABLE":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"بلیط با شناسه {t_id} در حال حاضر قابل رزرو نیست."
                )
            total_amount += Decimal(str(price))
            tickets_summary.append(TicketSummary(ticket_id=t_id, price=price))

        # ۲. محاسبه مهلت انقضا (۱۰ دقیقه آینده)
        expires_at = datetime.now() + timedelta(minutes=10)

        # ۳. ثبت رکورد اصلی در جدول reservations
        cursor.execute(
            """
            INSERT INTO reservations (user_id, total_amount, status, expires_at)
            VALUES (%s, %s, 'PENDING', %s)
            RETURNING reservation_id, created_at;
            """,
            (user_id, total_amount, expires_at)
        )
        res_row = cursor.fetchone()
        reservation_id = res_row["reservation_id"]
        created_at = res_row["created_at"]

        # ۴. ثبت رکوردهای آیتم رزرو در reservation_items
        for t_summary in tickets_summary:
            cursor.execute(
                """
                INSERT INTO reservation_items (reservation_id, ticket_id, price)
                VALUES (%s, %s, %s);
                """,
                (reservation_id, t_summary.ticket_id, t_summary.price)
            )

        # ۵. به‌روزرسانی وضعیت بلیط‌ها به HELD
        cursor.execute(
            """
            UPDATE tickets
            SET status = 'HELD'
            WHERE ticket_id = ANY(%s);
            """,
            (ticket_ids,)
        )

        # ۵. تایید نهایی تراکنش دیتابیس (Commit)
        conn.commit()

        return ReservationResponse(
            reservation_id=reservation_id,
            user_id=user_id,
            total_amount=total_amount,
            status="PENDING",
            expires_at=expires_at,
            created_at=created_at,
            tickets=tickets_summary
        )

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطای سرور هنگام ثبت رزرو: {str(e)}"
        )
    finally:
        cursor.close()
        conn.close()


# =========================================================================
# API شماره ۸: ثبت و نهایی‌سازی پرداخت (POST /reservations/payments)
# =========================================================================
@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_200_OK)
def process_payment(
    payload: PaymentCreate,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    reservation_id = payload.reservation_id

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # ۱. قفل‌گذاری و دریافت اطلاعات رزرو
        cursor.execute(
            """
            SELECT reservation_id, user_id, total_amount, status, expires_at
            FROM reservations
            WHERE reservation_id = %s
            FOR UPDATE;
            """,
            (reservation_id,)
        )
        res = cursor.fetchone()

        if not res:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="رزرو مورد نظر یافت نشد."
            )

        if res["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="شما مجاز به پرداخت این رزرو نیستید."
            )

        if res["status"] != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"امکان پرداخت وجود ندارد. وضعیت رزرو: {res['status']}"
            )

        # ۲. بررسی مهلت زمان ۱۰ دقیقه پرداخت
        if datetime.now() > res["expires_at"]:
            # انقضای مهلت: به‌روزرسانی وضعیت رزرو و آزاد کردن بلیط‌ها
            cursor.execute(
                "UPDATE reservations SET status = 'EXPIRED' WHERE reservation_id = %s;",
                (reservation_id,)
            )
            cursor.execute(
                """
                UPDATE tickets 
                SET status = 'AVAILABLE' 
                WHERE ticket_id IN (
                    SELECT ticket_id FROM reservation_items WHERE reservation_id = %s
                );
                """,
                (reservation_id,)
            )
            conn.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="مهلت ۱۰ دقیقه‌ای پرداخت منقضی شده است."
            )

        # ۳. تولید کد پیگیری یکتا
        tx_ref = f"TXN-{uuid.uuid4().hex[:10].upper()}"

        # ۴. ثبت رکورد پرداخت
        cursor.execute(
            """
            INSERT INTO payments (reservation_id, amount, payment_method, transaction_ref, status)
            VALUES (%s, %s, %s, %s, 'SUCCESSFUL')
            RETURNING payment_id, created_at;
            """,
            (reservation_id, res["total_amount"], payload.payment_method, tx_ref)
        )
        pay_row = cursor.fetchone()

        # ۵. به‌روزرسانی وضعیت رزرو به CONFIRMED
        cursor.execute(
            "UPDATE reservations SET status = 'CONFIRMED' WHERE reservation_id = %s;",
            (reservation_id,)
        )

        # ۶. تغییر وضعیت بلیط‌ها به SOLD
        cursor.execute(
            """
            UPDATE tickets 
            SET status = 'SOLD' 
            WHERE ticket_id IN (
                SELECT ticket_id FROM reservation_items WHERE reservation_id = %s
            );
            """,
            (reservation_id,)
        )

        # ۷. ثبت نهایی تراکنش دیتابیس
        conn.commit()

        return PaymentResponse(
            payment_id=pay_row["payment_id"],
            reservation_id=reservation_id,
            amount=res["total_amount"],
            payment_method=payload.payment_method,
            transaction_ref=tx_ref,
            status="SUCCESSFUL",
            created_at=pay_row["created_at"]
        )

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطا در پردازش پرداخت: {str(e)}"
        )
    finally:
        cursor.close()
        conn.close()


# =========================================================================
# API شماره ۱۱: دریافت تاریخچه خریدهای کاربر جاری (GET /reservations/me)
# =========================================================================
@router.get("/me", response_model=List[UserReservationHistory], status_code=status.HTTP_200_OK)
def get_my_reservations(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # ۱. دریافت تمام رزروهای متعلق به کاربر جاری
        cursor.execute(
            """
            SELECT reservation_id, total_amount, status, expires_at, created_at
            FROM reservations
            WHERE user_id = %s
            ORDER BY created_at DESC;
            """,
            (user_id,)
        )
        user_res_list = cursor.fetchall()

        result: List[UserReservationHistory] = []

        for r in user_res_list:
            res_id = r["reservation_id"]

            # ۲. دریافت جزئیات کامل بلیط‌ها، صندلی‌ها و مسابقات برای هر رزرو
            cursor.execute(
                """
                SELECT 
                    ri.ticket_id,
                    ri.price,
                    e.title AS event_title,
                    e.venue_name,
                    e.event_date,
                    s.section_name,
                    s.row_number,
                    s.seat_number
                FROM reservation_items ri
                JOIN tickets t ON ri.ticket_id = t.ticket_id
                JOIN events e ON t.event_id = e.event_id
                JOIN seats s ON t.seat_id = s.seat_id
                WHERE ri.reservation_id = %s;
                """,
                (res_id,)
            )
            items_data = cursor.fetchall()

            items_list = [
                ReservationItemDetail(
                    ticket_id=item["ticket_id"],
                    price=item["price"],
                    event_title=item["event_title"],
                    venue_name=item["venue_name"],
                    event_date=item["event_date"],
                    section_name=item["section_name"],
                    row_number=item["row_number"],
                    seat_number=item["seat_number"]
                )
                for item in items_data
            ]

            result.append(
                UserReservationHistory(
                    reservation_id=res_id,
                    total_amount=r["total_amount"],
                    status=r["status"],
                    expires_at=r["expires_at"],
                    created_at=r["created_at"],
                    items=items_list
                )
            )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطا در دریافت تاریخچه رزروها: {str(e)}"
        )
    finally:
        cursor.close()
        conn.close()
