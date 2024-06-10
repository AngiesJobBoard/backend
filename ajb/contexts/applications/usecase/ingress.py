from email.message import Message

from ajb.contexts.applications.models import Application
from ajb.contexts.billing.billing_models import UsageType
from ajb.contexts.billing.usecase import CompanyBillingUsecase
from ajb.contexts.companies.email_ingress_webhooks.models import CompanyEmailIngress
from ajb.contexts.resumes.models import UserCreateResume


class ApplicationIngressUseCase:
    def __init__(self, main):
        self.main = main

    def process_email_application_ingress(
        self,
        ingress_email: Message,
        ingress_record: CompanyEmailIngress,
    ) -> list[Application]:
        created_applications = []
        if not ingress_email.is_multipart():
            raise ValueError("Email is not multipart")
        for part in ingress_email.walk():
            content_disposition = part.get("Content-Disposition")
            if not content_disposition or "attachment" not in content_disposition:
                continue
            if not ingress_record.job_id:
                continue
            created_application = self.main.creation.create_application_from_resume(
                UserCreateResume(
                    file_type=part.get_content_type(),
                    file_name=str(part.get_filename()),
                    resume_data=part.get_payload(decode=True),  # type: ignore
                    company_id=ingress_record.company_id,
                    job_id=ingress_record.job_id,
                )
            )
            created_applications.append(created_application)

        CompanyBillingUsecase(self.main.request_scope).increment_company_usage(
            company_id=ingress_record.company_id,
            incremental_usages={
                UsageType.EMAIL_INGRESS: len(created_applications),
            },
        )
        return created_applications
