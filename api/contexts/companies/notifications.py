from fastapi import APIRouter, Request, Depends

from ajb.base import QueryFilterParams, build_pagination_response
from ajb.contexts.companies.notifications.repository import (
    CompanyNotificationRepository,
)
from ajb.contexts.companies.notifications.models import (
    CompanyNotification,
    PaginatedCompanyNotifications,
)

router = APIRouter(
    tags=["Company Notifications"], prefix="/companies/{company_id}/notifications"
)


@router.get("/", response_model=PaginatedCompanyNotifications)
def get_notifications(
    request: Request, company_id: str, query: QueryFilterParams = Depends()
):
    """Gets all notifications"""
    results = CompanyNotificationRepository(
        request.state.request_scope,
        company_id=company_id,
    ).query(query)
    return build_pagination_response(
        results,
        query.page,
        query.page_size,
        request.url._url,
        PaginatedCompanyNotifications,
    )


@router.get("/{notification_id}", response_model=CompanyNotification)
def get_notification(request: Request, company_id: str, notification_id: str):
    """Gets a notification by id"""
    return CompanyNotificationRepository(
        request.state.request_scope,
        company_id=company_id,
    ).get(notification_id)


@router.patch("/{notification_id}/read")
def mark_notification_as_read(request: Request, company_id: str, notification_id: str):
    """Marks a notification as read"""
    return CompanyNotificationRepository(
        request.state.request_scope,
        company_id=company_id,
    ).update_fields(notification_id, is_read=True)


@router.patch("/read")
def mark_notifications_as_read(
    request: Request, company_id: str, notification_ids: list[str]
):
    """Marks multiple notifications as read"""
    return CompanyNotificationRepository(
        request.state.request_scope,
        company_id=company_id,
    ).update_many(
        {notification_id: {"is_read": True} for notification_id in notification_ids}
    )


@router.patch("/{notification_id}/unread")
def mark_notification_as_unread(
    request: Request, company_id: str, notification_id: str
):
    """Marks a notification as unread"""
    return CompanyNotificationRepository(
        request.state.request_scope,
        company_id=company_id,
    ).update_fields(notification_id, is_read=False)


@router.patch("/unread")
def mark_notifications_as_unread(
    request: Request, company_id: str, notification_ids: list[str]
):
    """Marks multiple notifications as unread"""
    return CompanyNotificationRepository(
        request.state.request_scope,
        company_id=company_id,
    ).update_many(
        {notification_id: {"is_read": False} for notification_id in notification_ids}
    )


@router.delete("/{notification_id}")
def delete_notification(request: Request, company_id: str, notification_id: str):
    """Deletes a notification"""
    return CompanyNotificationRepository(
        request.state.request_scope,
        company_id=company_id,
    ).delete(notification_id)


@router.delete("/")
def delete_notifications(
    request: Request, company_id: str, notification_ids: list[str]
):
    """Deletes multiple notifications"""
    return CompanyNotificationRepository(
        request.state.request_scope,
        company_id=company_id,
    ).delete_many(notification_ids)
