from ajb.base import Collection, RepoFilterParams, Pagination, BaseUseCase
from ajb.vendor.arango.models import Filter
from ajb.contexts.companies.notifications.models import (
    CreateCompanyNotification,
    CompanyNotification,
    NotificationType,
    SystemCreateCompanyNotification,
)


class CompanyNotificationUsecase(BaseUseCase):
    def _get_recruiter_id(self, company_id: str, user_id: str) -> str:
        recruiter_repo = self.get_repository(Collection.COMPANY_RECRUITERS)
        recruiter = recruiter_repo.get_one(company_id=company_id, user_id=user_id)
        return recruiter.id

    def create_company_notification(
        self,
        company_id: str,
        data: SystemCreateCompanyNotification,
        all_but_current_recruiter: bool = False,
    ) -> None:
        notification_repo = self.get_repository(Collection.COMPANY_NOTIFICATIONS)
        recruiter_repo = self.get_repository(Collection.COMPANY_RECRUITERS)
        company_recruiters = recruiter_repo.get_all(company_id=company_id)

        if all_but_current_recruiter:
            company_recruiters = [
                recruiter
                for recruiter in company_recruiters
                if recruiter.user_id != self.request_scope.user_id
            ]

        documents = [
            CreateCompanyNotification(recruiter_id=recruiter.id, **data.model_dump())
            for recruiter in company_recruiters
        ]
        notification_repo.create_many(documents)

    def get_recruiter_notifications(
        self,
        company_id: str,
        user_id: str,
        notification_type: NotificationType | None = None,
        page: int = 0,
        page_size: int = 10,
    ) -> tuple[list[CompanyNotification], int]:
        notification_repo = self.get_repository(Collection.COMPANY_NOTIFICATIONS)
        recruiter_id = self._get_recruiter_id(company_id=company_id, user_id=user_id)
        query = RepoFilterParams(
            pagination=Pagination(page=page, page_size=page_size),
            filters=[
                Filter(field="recruiter_id", value=recruiter_id),
                Filter(field="company_id", value=company_id),
            ],
        )
        if notification_type:
            query.filters.append(
                Filter(field="notification_type", value=notification_type)
            )
        return notification_repo.query(repo_filters=query)

    def mark_all_recruiter_notifications_as_read(
        self, company_id: str, user_id: str
    ) -> bool:
        notification_repo = self.get_repository(Collection.COMPANY_NOTIFICATIONS)
        recruiter_id = self._get_recruiter_id(company_id=company_id, user_id=user_id)
        all_recruiter_notifications = notification_repo.get_all(
            recruiter_id=recruiter_id,
            is_read=False,
        )
        for notification in all_recruiter_notifications:
            notification_repo.update_fields(notification.id, is_read=True)
        return True

    def mark_one_recruiter_notification_as_read(
        self, company_id: str, notification_id: str
    ) -> bool:
        notification_repo = self.get_repository(
            Collection.COMPANY_NOTIFICATIONS, self.request_scope, company_id
        )
        notification_repo.update_fields(notification_id, is_read=True)
        return True
