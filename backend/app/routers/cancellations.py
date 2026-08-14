from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.cancellation import (
    PenaltyCheckResponseSchema,
    CancellationRequestCreateSchema,
    CancellationRequestResponseSchema,
)
from app.core.database import execute_query
from app.core.dependencies import get_current_user


router = APIRouter(
    prefix="/cancellations",
    tags=["Cancellations & Refunds"]
)


# ============================================================
# API: بررسی جریمه کنسلی (پیش‌نمایش محاسبات مالی)
# ============================================================

@router.get(
    "/penalty-check/{reservation_id}",
    response_model=PenaltyCheckResponseSchema
)
def calculate_cancellation_penalty(
    reservation_id: int,
    current_user: dict = Depends(get_current_user)
):

    # ۱. دریافت رزرو + بلیت + مسابقه
    query = """
        SELECT
            r.reservation_id,
            r.quantity,
            r.total_price,
            r.status AS res_status,
            t.price AS unit_price,
            m.match_datetime,
            m.organizer_id,
            m.sport_type_id
        FROM RESERVATIONS r
        INNER JOIN TICKETS t ON r.ticket_id = t.ticket_id
        INNER JOIN MATCHES m ON t.match_id = m.match_id
        WHERE r.reservation_id = %s AND r.user_id = %s;
    """

    user_id = current_user["user_id"]
    res = execute_query(query, (reservation_id, user_id), fetch_all=True)

    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="رزرو مورد نظر یافت نشد یا به آن دسترسی ندارید."
        )

    reservation = res[0]

    # ۲. فقط رزروهای paid قابل لغو هستند
    if reservation["res_status"] != "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="تنها رزروهای پرداخت‌شده قابل محاسبه جریمه کنسلی هستند."
        )

    # ۳. بررسی زمان مسابقه (مستقل از Naive/Aware بودن Timezone)
    match_dt = reservation["match_datetime"]
    
    # هم‌سان‌سازی تایم‌زون‌ها برای مقایسه بدون خطا
    if match_dt.tzinfo is not None:
        now = datetime.now(timezone.utc)
    else:
        now = datetime.now()

    if now >= match_dt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="امکان لغو بلیت پس از برگزاری یا در زمان برگزاری مسابقه وجود ندارد."
        )

    hours_remaining = (match_dt - now).total_seconds() / 3600.0

    # ۴. استعلام قوانین جریمه بر اساس برگزارکننده و نوع ورزش
    rule_query = """
        SELECT cpr.penalty_percent
        FROM CANCELLATION_POLICIES cp
        INNER JOIN CANCELLATION_POLICY_RULES cpr ON cp.policy_id = cpr.policy_id
        WHERE cp.organizer_id = %s
          AND cp.sport_type_id = %s
          AND cpr.min_hours <= %s
          AND (cpr.max_hours IS NULL OR cpr.max_hours >= %s)
        ORDER BY cpr.min_hours DESC
        LIMIT 1;
    """

    rules = execute_query(
        rule_query,
        (
            reservation["organizer_id"],
            reservation["sport_type_id"],
            hours_remaining,
            hours_remaining,
        ), 
        fetch_all=True
    )

    # ۵. تعیین درصد جریمه (در صورت عدم وجود قانون، ۲۰ درصد پیش‌فرض)
    penalty_percent = (
        float(rules[0]["penalty_percent"])
        if rules else 20.0
    )

    # ۶. محاسبات مالی
    total_price = float(reservation["total_price"])
    penalty_amount = round((total_price * penalty_percent) / 100.0, 2)
    refundable_amount = max(0.0, round(total_price - penalty_amount, 2))

    return {
        "reservation_id": reservation_id,
        "ticket_price": float(reservation["unit_price"]),
        "quantity": reservation["quantity"],
        "total_price": total_price,
        "hours_until_match": round(hours_remaining, 2),
        "penalty_percent": penalty_percent,
        "penalty_amount": penalty_amount,
        "refundable_amount": refundable_amount,
    }


# ============================================================
# API: ثبت درخواست کنسلی
# ============================================================

@router.post(
    "/request",
    response_model=CancellationRequestResponseSchema
)
def submit_cancellation_request(
    payload: CancellationRequestCreateSchema,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]

    # ۱. بررسی وجود رزرو، مالکیت کاربر و زمان مسابقه
    check_sql = """
        SELECT
            r.status AS reservation_status,
            m.match_datetime
        FROM RESERVATIONS r
        INNER JOIN TICKETS t ON r.ticket_id = t.ticket_id
        INNER JOIN MATCHES m ON t.match_id = m.match_id
        WHERE r.reservation_id = %s
          AND r.user_id = %s;
    """

    res = execute_query(
        check_sql,
        (payload.reservation_id, user_id), 
        fetch_all=True
    )

    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="رزروی با این مشخصات متعلق به شما یافت نشد."
        )

    reservation = res[0]

    # ۲. بررسی وضعیت پرداخت
    if reservation["reservation_status"] != "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="رزرو انتخاب شده در وضعیت پرداخت‌شده قرار ندارد."
        )

    # ۳. بررسی زمان مسابقه
    match_dt = reservation["match_datetime"]
    if match_dt.tzinfo is not None:
        now = datetime.now(timezone.utc)
    else:
        now = datetime.now()

    if now >= match_dt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="امکان ثبت درخواست کنسلی پس از برگزاری مسابقه وجود ندارد."
        )

    # ۴. جلوگیری از ثبت درخواست تکراری در انتظار بررسی
    dup_check = """
        SELECT request_id
        FROM CANCELLATION_REQUESTS
        WHERE reservation_id = %s
          AND request_type = 'cancel'
          AND status = 'pending'
        LIMIT 1;
    """

    duplicate = execute_query(dup_check, (payload.reservation_id,), fetch_all=True)

    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="یک درخواست کنسلی در انتظار بررسی برای این رزرو قبلاً ثبت شده است."
        )

    # ۵. ثبت درخواست در جدول CANCELLATION_REQUESTS
    insert_sql = """
        INSERT INTO CANCELLATION_REQUESTS
        (
            reservation_id,
            user_id,
            request_type,
            status,
            user_note,
            requested_at
        )
        VALUES (%s, %s, 'cancel', 'pending', %s, NOW())
        RETURNING request_id, requested_at;
    """

    inserted = execute_query(
        insert_sql,
        (payload.reservation_id, user_id, payload.user_note), 
        fetch_all=True
    )

    if not inserted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="خطا در ثبت درخواست کنسلی در دیتابیس."
        )

    inserted_row = inserted[0]

    return {
        "request_id": inserted_row["request_id"],
        "reservation_id": payload.reservation_id,
        "status": "pending",
        "requested_at": inserted_row["requested_at"],
        "message": "درخواست کنسلی شما با موفقیت ثبت شد و پس از بررسی پشتیبانی، مبلغ به کیف پول شما واریز خواهد شد."
    }