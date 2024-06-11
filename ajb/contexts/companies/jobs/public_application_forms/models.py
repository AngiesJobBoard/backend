from datetime import datetime
from pydantic import BaseModel

from ajb.base import BaseDataModel


class Reference(BaseModel):
    name: str
    phone: str
    email: str
    company_and_position_title: str


class EmploymentHistory(BaseModel):
    hire_date: datetime
    ending_date: datetime
    ending_hourly_pay_rate: float
    manager_name: str
    manager_phone: str
    manager_email: str
    company_name: str
    job_duties: str
    reason_for_leaving: str


class UserCreatePublicApplicationForm(BaseModel):
    full_legal_name: str
    preferred_name: str
    email: str
    phone: str
    valid_drivers_license: bool
    over_18_years_old: bool
    legally_authorized_to_work_in_us: bool
    smoke_vape_chew_thc_products: bool
    willing_and_able_to_pass_drug_test: bool
    arrested_charged_convicted_of_felony: bool
    felony_details: str
    references: list[Reference]
    employment_history: list[EmploymentHistory]
    how_did_you_hear_about_us: str
    when_available_to_start: datetime
    desired_hourly_pay_rate: float | None = None
    worked_at_company_before: bool
    has_reliable_transportation: bool

    willing_to_submit_to_background_check: bool
    willing_to_submit_to_drug_test: bool
    willing_to_submit_to_driving_record_check: bool
    willing_to_submit_to_reference_check: bool

    confirm_all_statements_true: bool
    e_signature: str


class CreatePublicApplicationForm(UserCreatePublicApplicationForm):
    application_id: str | None = None
    job_id: str
    company_id: str


class PublicApplicationForm(CreatePublicApplicationForm, BaseDataModel):
    pass
