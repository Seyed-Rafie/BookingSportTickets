from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.report import CreateReportRequest, CreateReportResponse
from app.core.dependencies import get_current_user
from app.core.database import execute_query

router = APIRouter(prefix="/reports", tags=["Reports & Support"])

@router.post("", response_model=CreateReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(
    request: CreateReportRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    API 13: Submit a support report/ticket by authenticated user.
    """
    user_id = current_user["user_id"]

    # 1. Validate category existence in report_categories table
    cat_query = "SELECT report_category_id FROM report_categories WHERE report_category_id = %s LIMIT 1;"
    category = execute_query(cat_query, (request.report_category_id,), fetch_one=True)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid report category ID."
        )

    # 2. Validate reservation ownership if reservation_id is provided
    if request.reservation_id is not None:
        res_query = "SELECT reservation_id, user_id FROM reservations WHERE reservation_id = %s LIMIT 1;"
        reservation = execute_query(res_query, (request.reservation_id,), fetch_one=True)
        
        if not reservation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reservation not found."
            )
        
        # Check if reservation actually belongs to the authenticated user
        if reservation["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to report issues for this reservation."
            )

    # 3. Insert report into DB with default status 'pending'
    insert_query = """
        INSERT INTO reports (
            user_id, 
            ticket_id, 
            reservation_id, 
            report_category_id, 
            description, 
            status
        )
        VALUES (%s, %s, %s, %s, %s, 'pending')
        RETURNING report_id, user_id, ticket_id, reservation_id, report_category_id, description, status, submitted_at;
    """
    params = (
        user_id,
        request.ticket_id,
        request.reservation_id,
        request.report_category_id,
        request.description.strip()
    )

    # Execute mutation query with commit=True
    new_report = execute_query(insert_query, params, commit=True, fetch_one=True)

    return CreateReportResponse(
        report_id=new_report["report_id"],
        user_id=new_report["user_id"],
        ticket_id=new_report["ticket_id"],
        reservation_id=new_report["reservation_id"],
        report_category_id=new_report["report_category_id"],
        description=new_report["description"],
        status=new_report["status"],
        submitted_at=new_report["submitted_at"]
    )