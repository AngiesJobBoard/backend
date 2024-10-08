from email.message import Message

from ajb.base import BaseUseCase
from ajb.contexts.applications.models import Application
from ajb.contexts.companies.email_ingress_webhooks.models import CompanyEmailIngress
from ajb.contexts.resumes.models import UserCreateResume

from .create_application_from_resume import CreateApplicationFromResumeResolver


class ApplicationEmailIngressResolver(BaseUseCase):
    def _validate_email(self, ingress_email: Message) -> None:
        if not ingress_email.is_multipart():
            raise ValueError("Email is not multipart")

    def _create_application(
        self,
        resume_resolver: CreateApplicationFromResumeResolver,
        part: Message,
        ingress_record: CompanyEmailIngress,
    ) -> Application | None:
        if not ingress_record.job_id:
            return None
        return resume_resolver.create_application_from_resume(
            UserCreateResume(
                file_type=part.get_content_type(),
                file_name=str(part.get_filename()),
                resume_data=part.get_payload(decode=True),  # type: ignore
                company_id=ingress_record.company_id,
                job_id=ingress_record.job_id,
            )
        )

    def process_email_application_ingress(
        self,
        ingress_email: Message,
        ingress_record: CompanyEmailIngress,
    ) -> list[Application]:
        self._validate_email(ingress_email)
        resume_resolver = CreateApplicationFromResumeResolver(self.request_scope)

        created_applications = []
        for part in ingress_email.walk():
            content_disposition = part.get("Content-Disposition")
            if not content_disposition or "attachment" not in content_disposition:
                continue
            potential_created_application = self._create_application(
                resume_resolver, part, ingress_record
            )
            if potential_created_application:
                created_applications.append(potential_created_application)
        return created_applications
