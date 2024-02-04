from fastapi import APIRouter, Request, Depends

from ajb.base import QueryFilterParams, build_pagination_response
from ajb.contexts.users.notifications.repository import UserNotificationRepository
from ajb.contexts.users.notifications.models import (
    UserNotification,
    PaginatedUserNotifications,
)

router = APIRouter(tags=["User Notifications"], prefix="/notifications")


@router.get("/", response_model=PaginatedUserNotifications)
def get_notifications(request: Request, query: QueryFilterParams = Depends()):
    """Gets all notifications"""
    results = UserNotificationRepository(
        request.state.request_scope,
    ).query(query)
    return build_pagination_response(
        results,
        query.page,
        query.page_size,
        request.url._url,
        PaginatedUserNotifications,
    )


@router.get("/{notification_id}", response_model=UserNotification)
def get_notification(request: Request, notification_id: str):
    """Gets a notification by id"""
    return UserNotificationRepository(
        request.state.request_scope,
    ).get(notification_id)


@router.patch("/{notification_id}/read")
def mark_notification_as_read(request: Request, notification_id: str):
    """Marks a notification as read"""
    return UserNotificationRepository(
        request.state.request_scope,
    ).update_fields(notification_id, is_read=True)


@router.patch("/read")
def mark_notifications_as_read(request: Request, notification_ids: list[str]):
    """Marks multiple notifications as read"""
    return UserNotificationRepository(
        request.state.request_scope,
    ).update_many(
        {notification_id: {"is_read": True} for notification_id in notification_ids}
    )


@router.patch("/{notification_id}/unread")
def mark_notification_as_unread(request: Request, notification_id: str):
    """Marks a notification as unread"""
    return UserNotificationRepository(
        request.state.request_scope,
    ).update_fields(notification_id, is_read=False)


@router.patch("/unread")
def mark_notifications_as_unread(request: Request, notification_ids: list[str]):
    """Marks multiple notifications as unread"""
    return UserNotificationRepository(
        request.state.request_scope,
    ).update_many(
        {notification_id: {"is_read": False} for notification_id in notification_ids}
    )


@router.delete("/{notification_id}")
def delete_notification(request: Request, notification_id: str):
    """Deletes a notification"""
    return UserNotificationRepository(
        request.state.request_scope,
    ).delete(notification_id)


@router.delete("/")
def delete_notifications(request: Request, notification_ids: list[str]):
    """Deletes multiple notifications"""
    return UserNotificationRepository(
        request.state.request_scope,
    ).delete_many(notification_ids)
