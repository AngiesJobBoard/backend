from base64 import b64decode
from pydantic import BaseModel
from dateutil import parser as date_parser

from ajb.common.models import Location
from ajb.contexts.companies.jobs.public_application_forms.models import (
    UserCreatePublicApplicationForm,
)
from ajb.contexts.companies.jobs.public_application_forms.usecase import (
    JobPublicApplicationFormUsecase,
)
from ajb.contexts.resumes.models import UserCreateResume
from ajb.contexts.applications.models import CreateApplication
from ajb.contexts.applications.usecase import ApplicationUseCase
from ajb.vendor.pdf_plumber import extract_text
from transformers.incoming.base import BaseIncomingTransformer, CouldNotInferJobError


class FullName(BaseModel):
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None


class ContactInformation(BaseModel):
    job_name: str
    name: str | None = None
    full_name: FullName
    first_name: str | None = None
    last_name: str | None = None
    email: str
    phone: str | None = None
    phone_alt: str | None = None
    address: str | None = None
    city: str
    state: str
    zip: str
    full_address: str | None = None
    position_discovered: str | None = None
    position_referral: str | None = None
    seen_billboard: str | None = None
    date_available: str | None = None
    wage_amount: str | None = None
    wage_frequency: str | None = None
    age_18: str | None = None
    currently_employed: str | None = None
    us_work_authorized: str | None = None
    smoker: str | None = None
    drug_screening: str | None = None
    drug_test: str | None = None
    prior_application: str | None = None
    prior_application_details: str | None
    transportation: str | None = None
    transportation_details: str | None = None
    conviction: str | None = None
    conviction_details: str | None
    terminated: str | None
    terminated_details: str | None
    drivers_license_num: str | None
    drivers_license_state: str | None
    drivers_license_issued: str | None
    signed_consent_refereces: str | None = None
    signed_consent_testing: str | None = None
    signed_consent_drug_testing: str | None = None
    signed_consent_bg_check: str | None = None
    signed_auth_investigation: str | None = None
    signed_answers_true: str | None = None
    digital_signature: str | None = None


class PostCardManiaRawData(BaseModel):
    contact_information: ContactInformation
    resume_bytes: list[str]


class IncomingPostCardManiaTransformer(BaseIncomingTransformer[PostCardManiaRawData]):
    entity_model = PostCardManiaRawData

    def infer_job_from_raw_data(self):
        """For postcardmania, we will infer the job from the job name."""
        self.job_id = self.get_job_from_name(self.data.contact_information.job_name).id

    def transform_to_application_model(self):
        # AJBTODO complete the work history and education history which is sometimes ? included ?
        if not self.job_id:
            raise CouldNotInferJobError

        # Create application object
        info = self.data.contact_information
        application_data = CreateApplication(
            company_id=self.raw_data.company_id,
            job_id=self.job_id,
            name=f"{info.full_name.first_name} {info.full_name.last_name}",
            email=info.email,
            phone=info.phone,
            user_location=Location(
                city=info.city,
                state=info.state,
                zipcode=info.zip,
            ),
        )

        # Transform data into application form submission
        yes_values = [
            "yes",
            "true",
            "checked",
            "1",
        ]  # For converting unknown yes/no strings to boolean values

        application_form_data = UserCreatePublicApplicationForm(
            full_legal_name=f"{info.full_name.first_name} {info.full_name.last_name}",
            email=info.email,
            phone=info.phone,
            worked_at_company_before=info.prior_application.lower() in yes_values,
            valid_drivers_license=info.drivers_license_num is not None,
            over_18_years_old=info.age_18.lower() in yes_values,
            legally_authorized_to_work_in_us=info.us_work_authorized.lower()
            in yes_values,
            smoke_vape_chew_thc_products=info.smoker.lower() in yes_values,
            willing_and_able_to_pass_drug_test=info.drug_test.lower() in yes_values,
            arrested_charged_convicted_of_felony=info.conviction in yes_values,
            felony_details=info.conviction_details,
            references=[],
            how_did_you_hear_about_us=info.position_discovered,
            referral_name=info.position_referral,
            other_referral_source="",
            when_available_to_start=date_parser.parse(info.date_available),
            has_reliable_transportation=info.transportation.lower() in yes_values,
            alternative_to_reliable_transportation=info.transportation_details,
            willing_to_submit_to_background_check=info.signed_consent_bg_check.lower()
            in yes_values,
            willing_to_submit_to_drug_test=info.signed_consent_drug_testing.lower()
            in yes_values,
            confirm_all_statements_true=info.signed_answers_true.lower() in yes_values,
            willing_to_submit_to_reference_check=info.signed_consent_refereces.lower()
            in yes_values,
            e_signature=info.digital_signature,
            job_id=self.job_id,
            company_id=self.raw_data.company_id,
        )

        # Create application form object in the repository
        usecase = JobPublicApplicationFormUsecase(self.request_scope)
        usecase.submit_public_job_application(
            data=application_form_data, job_id=self.job_id
        )

        # Return the CreateApplication object as expected
        return application_data

    def create_application_from_resume(self):
        if not self.job_id:
            raise CouldNotInferJobError
        resume_data = b64decode(self.data.resume_bytes[0])
        return ApplicationUseCase(self.request_scope).create_application_from_resume(
            data=UserCreateResume(
                file_type="upload",
                file_name="webhook_resume",
                resume_data=resume_data,
                company_id=self.raw_data.company_id,
                job_id=self.job_id,
            ),
            additional_partial_data=CreateApplication(
                company_id=self.raw_data.company_id,
                job_id=self.job_id,
                name=f"{self.data.contact_information.full_name.first_name} {self.data.contact_information.full_name.last_name}",
                email=self.data.contact_information.email,
                phone=self.data.contact_information.phone,
                user_location=Location(
                    city=self.data.contact_information.city,
                    state=self.data.contact_information.state,
                    zipcode=self.data.contact_information.zip,
                ),
                extracted_resume_text=extract_text(resume_data),
            ),
        )

    def create_application_from_data(self):
        if not self.job_id:
            raise CouldNotInferJobError
        return ApplicationUseCase(self.request_scope).create_application(
            company_id=self.raw_data.company_id,
            job_id=self.job_id,
            partial_application=self.transform_to_application_model(),
        )

    def create_application(self):
        if self.data.resume_bytes and self.data.resume_bytes[0]:
            return self.create_application_from_resume()
        return self.create_application_from_data()
