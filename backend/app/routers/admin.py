from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from app.schemas.admin import ReportResponseUpdate, ReservationStatusUpdate, AdminReportResponse
from app.core.dependencies import get_current_support_user
from app.core.database import execute_query

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