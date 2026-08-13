from datetime import datetime, timedelta
from decimal import Decimal
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extras import RealDictCursor

from app.core.database import get_db_connection
from app.core.dependencies import get_current_user
from app.schemas.reservation import (
    ReservationCreate,
    ReservationResponse,
    PaymentCreate,
    PaymentResponse,
    UserReservationHistory,
    ReservationSeatDetail,
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
    ticket_id = payload.ticket_id
    seat_ids = payload.seat_ids
    quantity = len(seat_ids)

    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            # ۱. بررسی وجود و قیمت بلیط
            cursor.execute(
                "SELECT price, remaining_capacity, status FROM TICKETS WHERE ticket_id = %s FOR UPDATE;",
                (ticket_id,)
            )
            ticket = cursor.fetchone()

            if not ticket:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="بلیط مورد نظر یافت نشد.")

            if ticket["remaining_capacity"] < quantity:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ظرفیت بلیط کافی نیست.")

            # ۲. بررسی آماده رزرو بودن صندلی‌های انتخابی
            cursor.execute(
                "SELECT seat_id, status FROM SEATS WHERE seat_id = ANY(%s) AND ticket_id = %s FOR UPDATE;",
                (seat_ids, ticket_id)
            )
            seats = cursor.fetchall()

            if len(seats) != quantity:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="یک یا چند صندلی انتخابی معتبر نیستند.")

            for s in seats:
                if s["status"] != "available":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"صندلی با شناسه {s['seat_id']} قبلاً رزرو یا فروخته شده است."
                    )

            # ۳. محاسبه مبلغ کل و مهلت ۱۰ دقیقه‌ای
            total_price = Decimal(str(ticket["price"])) * quantity
            reserved_at = datetime.now()
            reserved_until = reserved_at + timedelta(minutes=10)

            # ۴. ایجاد رکورد اصلی در جدول RESERVATIONS
            cursor.execute(
                """
                INSERT INTO RESERVATIONS (user_id, ticket_id, quantity, status, total_price, reserved_at, reserved_until)
                VALUES (%s, %s, %s, 'reserved', %s, %s, %s)
                RETURNING reservation_id;
                """,
                (user_id, ticket_id, quantity, total_price, reserved_at, reserved_until)
            )
            res_row = cursor.fetchone()
            reservation_id = res_row["reservation_id"]

            # ۵. قفل صندلی‌ها در RESERVED_SEATS و آپدیت وضعیت صندلی‌ها به 'reserved'
            for s_id in seat_ids:
                cursor.execute(
                    "INSERT INTO RESERVED_SEATS (reservation_id, seat_id, status) VALUES (%s, %s, 'active');",
                    (reservation_id, s_id)
                )
                cursor.execute(
                    "UPDATE SEATS SET status = 'reserved' WHERE seat_id = %s;",
                    (s_id,)
                )

            # ۶. کاهش ظرفیت باقی‌مانده بلیط
            cursor.execute(
                "UPDATE TICKETS SET remaining_capacity = remaining_capacity - %s WHERE ticket_id = %s;",
                (quantity, ticket_id)
            )

            conn.commit()

            return ReservationResponse(
                reservation_id=reservation_id,
                user_id=user_id,
                ticket_id=ticket_id,
                quantity=quantity,
                status="reserved",
                total_price=total_price,
                reserved_at=reserved_at,
                reserved_until=reserved_until,
                seat_ids=seat_ids
            )

        except HTTPException:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"خطا در ایجاد رزرو: {str(e)}"
            )
        finally:
            cursor.close()


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

    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            # ۱. قفل رزرو جهت بررسی وضعیت
            cursor.execute(
                """
                SELECT reservation_id, user_id, ticket_id, quantity, status, total_price, reserved_until
                FROM RESERVATIONS
                WHERE reservation_id = %s
                FOR UPDATE;
                """,
                (reservation_id,)
            )
            res = cursor.fetchone()

            if not res:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="رزرو یافت نشد.")

            if res["user_id"] != user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="دسترسی غیرمجاز.")

            if res["status"] != "reserved":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"امکان پرداخت وجود ندارد. وضعیت فعلی: {res['status']}"
                )

            # ۲. بررسی مهلت زمان ۱۰ دقیقه
            if datetime.now() > res["reserved_until"]:
                # آزادکن صندلی‌ها و انقضای رزرو
                cursor.execute("UPDATE RESERVATIONS SET status = 'expired' WHERE reservation_id = %s;", (reservation_id,))
                cursor.execute("UPDATE RESERVED_SEATS SET status = 'released' WHERE reservation_id = %s;", (reservation_id,))
                cursor.execute(
                    """
                    UPDATE SEATS SET status = 'available'
                    WHERE seat_id IN (SELECT seat_id FROM RESERVED_SEATS WHERE reservation_id = %s);
                    """,
                    (reservation_id,)
                )
                cursor.execute(
                    "UPDATE TICKETS SET remaining_capacity = remaining_capacity + %s WHERE ticket_id = %s;",
                    (res["quantity"], res["ticket_id"])
                )
                conn.commit()
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="مهلت ۱۰ دقیقه‌ای پرداخت منقضی شده است.")

            # ۳. ثبت پرداخت
            tx_code = f"TXN-{uuid.uuid4().hex[:10].upper()}"
            paid_at = datetime.now()

            cursor.execute(
                """
                INSERT INTO PAYMENTS (reservation_id, amount, method, status, paid_at, transaction_code)
                VALUES (%s, %s, %s, 'success', %s, %s)
                RETURNING payment_id;
                """,
                (reservation_id, res["total_price"], payload.method, paid_at, tx_code)
            )
            pay_row = cursor.fetchone()

            # ۴. نهایی‌سازی وضعیت رزرو و صندلی‌ها به 'paid' و 'sold'
            cursor.execute("UPDATE RESERVATIONS SET status = 'paid' WHERE reservation_id = %s;", (reservation_id,))
            cursor.execute(
                """
                UPDATE SEATS SET status = 'sold'
                WHERE seat_id IN (SELECT seat_id FROM RESERVED_SEATS WHERE reservation_id = %s);
                """,
                (reservation_id,)
            )

            conn.commit()

            return PaymentResponse(
                payment_id=pay_row["payment_id"],
                reservation_id=reservation_id,
                amount=res["total_price"],
                method=payload.method,
                status="success",
                paid_at=paid_at,
                transaction_code=tx_code
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


# =========================================================================
# API شماره ۱۱: دریافت تاریخچه خریدهای کاربر جاری (GET /reservations/me)
# =========================================================================
@router.get("/me", response_model=List[UserReservationHistory], status_code=status.HTTP_200_OK)
def get_my_reservations(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]

    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            # ۱. استخراج رزروهای کاربر به همراه اطلاعات مسابقه و ورزشگاه
            cursor.execute(
                """
                SELECT 
                    r.reservation_id,
                    r.total_price,
                    r.status,
                    r.reserved_at,
                    r.reserved_until,
                    m.match_datetime,
                    v.name AS venue_name,
                    ht.name AS home_team,
                    at.name AS away_team
                FROM RESERVATIONS r
                JOIN TICKETS t ON r.ticket_id = t.ticket_id
                JOIN MATCHES m ON t.match_id = m.match_id
                JOIN VENUES v ON m.venue_id = v.venue_id
                JOIN TEAMS ht ON m.home_team_id = ht.team_id
                JOIN TEAMS at ON m.away_team_id = at.team_id
                WHERE r.user_id = %s
                ORDER BY r.reserved_at DESC;
                """,
                (user_id,)
            )
            reservations = cursor.fetchall()

            result: List[UserReservationHistory] = []

            for r in reservations:
                res_id = r["reservation_id"]

                # ۲. دریافت صندلی‌های هر رزرو
                cursor.execute(
                    """
                    SELECT s.seat_id, s.section, s.row_number, s.seat_number
                    FROM RESERVED_SEATS rs
                    JOIN SEATS s ON rs.seat_id = s.seat_id
                    WHERE rs.reservation_id = %s;
                    """,
                    (res_id,)
                )
                seats_data = cursor.fetchall()

                seat_list = [
                    ReservationSeatDetail(
                        seat_id=st["seat_id"],
                        section=st["section"],
                        row=st["row_number"],
                        seat_number=st["seat_number"]
                    )
                    for st in seats_data
                ]

                result.append(
                    UserReservationHistory(
                        reservation_id=res_id,
                        match_title=f"{r['home_team']} - {r['away_team']}",
                        venue_name=r["venue_name"],
                        match_datetime=r["match_datetime"],
                        total_price=r["total_price"],
                        status=r["status"],
                        reserved_at=r["reserved_at"],
                        reserved_until=r["reserved_until"],
                        seats=seat_list
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
