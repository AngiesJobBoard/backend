from fastapi import APIRouter, Request

from ajb.base import build_pagination_response
from ajb.contexts.companies.notifications.usecase import CompanyNotificationUsecase
from ajb.contexts.companies.notifications.models import (
    PaginatedCompanyNotifications,
    NotificationType,
)
from api.middleware import scope

router = APIRouter(
    tags=["Company Notifications"], prefix="/companies/{company_id}/notifications"
)


@router.get("/", response_model=PaginatedCompanyNotifications)
def get_notifications(
    request: Request,
    company_id: str,
    notification_type: NotificationType | None = None,
    page: int = 0,
    page_size: int = 10,
):
    """Gets all notifications"""
    results = CompanyNotificationUsecase(
        scope(request),
    ).get_recruiter_notifications(
        company_id,
        scope(request).user_id,
        notification_type=notification_type,
        page=page,
        page_size=page_size,
    )
    return build_pagination_response(
        results,
        page,
        page_size,
        request.url._url,
        PaginatedCompanyNotifications,
    )


@router.post("/mark_all_read")
def mark_all_notifications_as_read(request: Request, company_id: str):
    """Marks all notifications as read"""
    return CompanyNotificationUsecase(
        scope(request),
    ).mark_all_recruiter_notifications_as_read(company_id, scope(request).user_id)


@router.post("/mark_read")
def mark_notification_as_read(request: Request, company_id: str, notification_id: str):
    """Marks a notification as read"""
    return CompanyNotificationUsecase(
        scope(request),
    ).mark_one_recruiter_notification_as_read(company_id, notification_id)
