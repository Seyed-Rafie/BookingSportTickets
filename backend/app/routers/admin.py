import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from app.schemas.admin import ReportResponseUpdate, ReservationStatusUpdate, AdminReportResponse
from app.schemas.ticket import TicketSummarySchema, CreateTicketRequest, MatchSchema
from app.schemas.cancellation import CancellationRequestSummaryResponse, CancellationRequestDetailResponse, CancellationRequestReviewInput
from app.core.dependencies import get_current_support_user
from app.core.database import execute_query
from app.core.dependencies import get_current_admin_user
from app.core.elasticsearch import fetch_enriched_ticket, sync_ticket_to_es

router = APIRouter(prefix="/admin", tags=["Admin & Support Panel"])

# ---------------------------------------------------------
# 1. GET LIST OF REPORTS (WITH OPTIONAL STATUS FILTER)
# ---------------------------------------------------------
@router.get("/reports", response_model=List[AdminReportResponse])
def get_reports(
    report_status: Optional[str] = Query(None, alias="status", examples=["pending", "under_review", "resolved", "rejected"]),
    support_user: dict = Depends(get_current_support_user)
):
    """
    API 10 - Part 1: Retrieve submitted user reports with optional status filtering.
    """
    if report_status:
        query = """
            SELECT report_id, user_id, ticket_id, reservation_id, report_category_id,
                   description, status, reviewed_by_support_id, admin_response, submitted_at
            FROM reports
            WHERE status = %s
            ORDER BY submitted_at DESC;
        """
        reports = execute_query(query, (report_status,), fetch_all=True)
    else:
        query = """
            SELECT report_id, user_id, ticket_id, reservation_id, report_category_id,
                   description, status, reviewed_by_support_id, admin_response, submitted_at
            FROM reports
            ORDER BY submitted_at DESC;
        """
        reports = execute_query(query, fetch_all=True)

    return reports or []


# ---------------------------------------------------------
# 2. RESPOND TO AND UPDATE REPORT STATUS
# ---------------------------------------------------------
@router.patch("/reports/{report_id}", response_model=AdminReportResponse)
def respond_to_report(
    report_id: int,
    request: ReportResponseUpdate,
    support_user: dict = Depends(get_current_support_user)
):
    """
    API 10 - Part 2: Submit support response and update report status.
    """
    support_id = support_user["user_id"]

    # Check if report exists
    check_query = "SELECT report_id FROM reports WHERE report_id = %s LIMIT 1;"
    existing_report = execute_query(check_query, (report_id,), fetch_one=True)
    
    if not existing_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found."
        )

    # Update report response, status, and reviewed_by_support_id
    update_query = """
        UPDATE reports
        SET admin_response = %s,
            status = %s,
            reviewed_by_support_id = %s
        WHERE report_id = %s
        RETURNING report_id, user_id, ticket_id, reservation_id, report_category_id,
                  description, status, reviewed_by_support_id, admin_response, submitted_at;
    """
    params = (
        request.admin_response.strip(),
        request.status.strip(),
        support_id,
        report_id
    )

    updated_report = execute_query(update_query, params, commit=True, fetch_one=True)
    return updated_report


# ---------------------------------------------------------
# 3. MANUALLY UPDATE RESERVATION STATUS
# ---------------------------------------------------------
@router.patch("/reservations/{reservation_id}")
def update_reservation_status(
    reservation_id: int,
    request: ReservationStatusUpdate,
    support_user: dict = Depends(get_current_support_user)
):
    """
    API 10 - Part 3: Allow support/admin to override reservation status.
    """
    valid_statuses = ["reserved", "paid", "cancelled", "expired"]
    new_status = request.status.strip().lower()

    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Allowed values: {', '.join(valid_statuses)}"
        )

    # Check if reservation exists
    check_query = "SELECT reservation_id FROM reservations WHERE reservation_id = %s LIMIT 1;"
    reservation = execute_query(check_query, (reservation_id,), fetch_one=True)

    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found."
        )

    # Update reservation status in DB
    update_query = """
        UPDATE reservations
        SET status = %s
        WHERE reservation_id = %s
        RETURNING reservation_id, user_id, ticket_id, quantity, status, total_price, reserved_at, reserved_until;
    """
    updated_reservation = execute_query(update_query, (new_status, reservation_id), commit=True, fetch_one=True)

    return {
        "message": f"Reservation status updated to '{new_status}' successfully.",
        "reservation": updated_reservation
    }

@router.post("/ticket", response_model=TicketSummarySchema, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    request: CreateTicketRequest, 
    admin_user: dict = Depends(get_current_admin_user)
):
    # ۱. تولید کد یکتای بلیط
    ticket_code = f"TKN-{uuid.uuid4().hex[:8].upper()}"

    # ۲. درج در دیتابیس (مقدار اولیه remaining_capacity برابر با total_capacity است)
    insert_query = """
        INSERT INTO tickets (match_id, category_id, total_capacity, price, ticket_code)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING ticket_id;
    """
    
    result = execute_query(
        insert_query, 
        (
            request.match_id, 
            request.category_id, 
            request.total_capacity, 
            request.price, 
            ticket_code
        ), 
        fetch_one=True,
        commit=True
    )

    if not result:
        raise HTTPException(status_code=400, detail="خطا در ثبت بلیط")

    ticket_id = result["ticket_id"]

    # ۳. همگام‌سازی لحظه‌ای با Elasticsearch
    await sync_ticket_to_es(ticket_id)

    # ۴. دریافت داده غنی‌شده (همراه با اطلاعات کامل مسابقه و دسته‌بندی برای MatchSchema)
    enriched_data = await fetch_enriched_ticket(ticket_id)
    if not enriched_data:
        raise HTTPException(status_code=404, detail="اطلاعات بلیط ثبت‌شده یافت نشد")

    # ۵. ساخت خروجی منطبق با TicketSummarySchema
    return TicketSummarySchema(
        ticket_id=enriched_data["ticket_id"],
        ticket_code=enriched_data["ticket_code"],
        category_name=enriched_data["category_name"],
        price=float(enriched_data["price"]),
        remaining_capacity=enriched_data["remaining_capacity"],
        status=enriched_data["ticket_status"],
        match={
            "match_id": enriched_data["match_id"],
            "competition_name": enriched_data.get("competition_name", ""),
            "sport_type_name": enriched_data.get("sport_type", ""),
            "home_team": {"team_id": enriched_data.get("home_team_id", 0), "name": enriched_data.get("home_team", "")},
            "away_team": {"team_id": enriched_data.get("away_team_id", 0), "name": enriched_data.get("away_team", "")},
            "venue_name": enriched_data.get("venue_name", ""),
            "city_name": enriched_data.get("city", ""),
            "match_datetime": enriched_data.get("event_date"),
            "status": enriched_data.get("match_status", "")
        }
    )   

# ---------------------------------------------------------
# API 1: GET LIST OF CANCELLATION REQUESTS (WITH STATUS FILTER)
# ---------------------------------------------------------
@router.get(
    "/cancellation-requests", 
    response_model=List[CancellationRequestSummaryResponse],
    status_code=status.HTTP_200_OK
)
def get_cancellation_requests(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by: pending, approved, rejected"),
    support_user: dict = Depends(get_current_support_user)
):
    """
    API 1: Retrieve summary list of all cancellation/change-seat requests.
    Supports optional status filtering (pending, approved, rejected).
    """
    if status_filter:
        query = """
            SELECT 
                request_id, 
                reservation_id, 
                user_id, 
                request_type, 
                status, 
                reviewed_by_support_id, 
                requested_new_seat_id, 
                user_note, 
                admin_note, 
                requested_at
            FROM cancellation_requests
            WHERE status = %s
            ORDER BY requested_at DESC;
        """
        results = execute_query(query, (status_filter.strip(),), fetch_all=True)
    else:
        query = """
            SELECT 
                request_id, 
                reservation_id, 
                user_id, 
                request_type, 
                status, 
                reviewed_by_support_id, 
                requested_new_seat_id, 
                user_note, 
                admin_note, 
                requested_at
            FROM cancellation_requests
            ORDER BY requested_at DESC;
        """
        results = execute_query(query, fetch_all=True)

    return results or []

# ---------------------------------------------------------
# API 2: GET DETAILED CANCELLATION REQUEST BY ID
# ---------------------------------------------------------
@router.get(
    "/cancellation-requests/{request_id}",
    response_model=CancellationRequestDetailResponse,
    status_code=status.HTTP_200_OK
)
def get_cancellation_request_detail(
    request_id: int,
    support_user: dict = Depends(get_current_support_user)
):
    """
    API 2: Retrieve full details of a specific cancellation or seat-change request.
    Includes current status of the associated reservation for admin context.
    """
    query = """
        SELECT 
            cr.request_id, 
            cr.reservation_id, 
            cr.user_id, 
            cr.request_type, 
            cr.status, 
            cr.reviewed_by_support_id, 
            cr.requested_new_seat_id, 
            cr.user_note, 
            cr.admin_note, 
            cr.requested_at,
            r.status AS reservation_status
        FROM cancellation_requests cr
        LEFT JOIN reservations r ON cr.reservation_id = r.reservation_id
        WHERE cr.request_id = %s
        LIMIT 1;
    """
    request_detail = execute_query(query, (request_id,), fetch_one=True)

    if not request_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cancellation request not found."
        )

    return request_detail

# ---------------------------------------------------------
# API 3: REVIEW AND RESPOND TO CANCELLATION REQUEST (PATCH)
# ---------------------------------------------------------
@router.patch(
    "/cancellation-requests/{request_id}",
    response_model=CancellationRequestDetailResponse,
    status_code=status.HTTP_200_OK
)
def review_cancellation_request(
    request_id: int,
    payload: CancellationRequestReviewInput,
    support_user: dict = Depends(get_current_support_user)
):
    """
    API 3: Admin responds to a cancellation/change-seat request (Approve or Reject).
    Updates request status, records support admin ID, and updates associated reservation if approved.
    """
    # 1. بررسی وجود درخواست و معتبر بودن وضعیت فعلی آن
    check_query = """
        SELECT request_id, reservation_id, request_type, status, requested_new_seat_id
        FROM cancellation_requests
        WHERE request_id = %s
        LIMIT 1;
    """
    existing_request = execute_query(check_query, (request_id,), fetch_one=True)

    if not existing_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cancellation request not found."
        )

    if existing_request['status'] != 'pending':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This request has already been processed with status '{existing_request['status']}'."
        )

    support_id = support_user.get("user_id") or support_user.get("id")

    # 2. بروزرسانی جدول CANCELLATION_REQUESTS
    update_request_query = """
        UPDATE cancellation_requests
        SET 
            status = %s,
            admin_note = %s,
            reviewed_by_support_id = %s
        WHERE request_id = %s;
    """
    execute_query(
        update_request_query, 
        (payload.status, payload.admin_note, support_id, request_id),
        commit=True
    )

    # 3. اعمال تغییرات روی جدول RESERVATIONS در صورت تایید (Approved)
    reservation_id = existing_request['reservation_id']
    if payload.status == 'approved':
        if existing_request['request_type'] == 'cancel':
            # لغو رزرو
            update_res_query = "UPDATE reservations SET status = 'cancelled' WHERE reservation_id = %s;"
            execute_query(update_res_query, (reservation_id,), commit=True)
            
        elif existing_request['request_type'] == 'change_seat' and existing_request['requested_new_seat_id']:
            # تغییر صندلی رزرو
            update_seat_query = "UPDATE reservations SET seat_id = %s WHERE reservation_id = %s;"
            execute_query(update_seat_query, (existing_request['requested_new_seat_id'], reservation_id), commit=True)

    # 4. دریافت و بازگرداندن نتیجه نهایی
    return get_cancellation_request_detail(request_id=request_id, support_user=support_user)