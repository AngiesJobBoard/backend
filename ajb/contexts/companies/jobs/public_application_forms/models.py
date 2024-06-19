from datetime import datetime
from pydantic import BaseModel

from ajb.base import BaseDataModel


class Reference(BaseModel):
    name: str
    phone: str
    email: str
    company_and_position_title: str


class UserCreatePublicApplicationForm(BaseModel):
    full_legal_name: str
    email: str
    phone: str
    worked_at_company_before: bool | None
    valid_drivers_license: bool | None
    over_18_years_old: bool | None
    legally_authorized_to_work_in_us: bool | None
    smoke_vape_chew_thc_products: bool | None
    willing_and_able_to_pass_drug_test: bool | None
    arrested_charged_convicted_of_felony: bool | None
    felony_details: str
    references: list[Reference]
    how_did_you_hear_about_us: str
    referral_name: str
    other_referral_source: str
    when_available_to_start: datetime
    has_reliable_transportation: bool | None
    alternative_to_reliable_transportation: str
    willing_to_submit_to_background_check: bool | None
    willing_to_submit_to_drug_test: bool | None
    willing_to_submit_to_reference_check: bool | None
    confirm_all_statements_true: bool | None
    e_signature: str


class CreatePublicApplicationForm(UserCreatePublicApplicationForm):
    application_id: str | None = None
    job_id: str
    company_id: str


class PublicApplicationForm(CreatePublicApplicationForm, BaseDataModel):
    pass
