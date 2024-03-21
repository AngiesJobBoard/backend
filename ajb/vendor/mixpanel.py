"""
This modules handles the integration with Mixpanel to track different events throughout the system.
It contains both the vendor class MixpanelService and the DomainEvents class that extends it to handle the different events.
While it does look like it overlaps with other event handling (like through kafka) we are keeping this separate
so that we don't have to extend the definition of an event related to kafka. This is more for tracking user behavior
and not for system events.
"""
from typing import Literal
import threading
from enum import Enum
from mixpanel import Mixpanel
from ajb.config.settings import SETTINGS


class MixpanelService:
    def __init__(self):
        self.mp: Mixpanel | None = None
        if SETTINGS.MIXPANEL_TOKEN:
            self.mp = Mixpanel(SETTINGS.MIXPANEL_TOKEN)

    def track(self, user_id: str, company_id: str | None,  event: str, properties: dict = {}):
        threading.Thread(target=self._track, args=(user_id, company_id, event, properties)).start()

    def _track(self, user_id: str, company_id: str | None,  event: str, properties: dict = {}):
        if company_id:
            properties["company_id"] = company_id
        if self.mp:
            self.mp.track(user_id, event, properties)

    def update_user_profile(self, user_id: str, properties: dict):
        if self.mp:
            self.mp.people_set(user_id, properties)

    def update_company_profile(self, company_id: str, properties: dict):
        if self.mp:
            self.mp.group_set(group_key="company_id", group_id=company_id, properties=properties)



class EventName(str, Enum):
    USER_CREATED = "user_created"
    COMPANY_CREATED = "company_created"
    RECRUITER_IS_INVITED_TO_COMPANY = "recruiter_is_invited_to_company"
    RECRUITER_INVITATION_IS_ACCEPTED = "recruiter_invitation_is_accepted"
    JOB_DESCRIPTION_IS_GENERATED = "job_description_is_generated"
    RESUME_IS_SCANNED = "resume_is_scanned"
    JOB_CREATED_FROM_PORTAL = "job_created_from_portal"
    JOB_CREATED_FROM_EMAIL_INGRESS = "job_created_from_email_ingress"
    JOB_CREATED_FROM_API_WEBHOOK_INGRESS = "job_created_from_api_webhook_ingress"
    APPLICATION_IS_SUBMITTED_AND_ENRICHED = "application_is_submitted_and_enriched"
    APPLICATION_CREATED_FROM_PORTAL = "application_created_from_portal"
    APPLICATION_CREATED_FROM_EMAIL_INGRESS = "application_created_from_email_ingress"
    APPLICATION_CREATED_FROM_API_WEBHOOK_INGRESS = "application_created_from_api_webhook_ingress"
    APPLICATION_IS_SHORTLISTED = "application_is_shortlisted"
    APPLICATION_IS_DELETED = "application_is_deleted"
    APPLICATION_STATUS_IS_UPDATED = "application_status_is_updated"
    APPLICATION_IS_VIEWED = "application_is_viewed"
    JOB_FORWARDED_FROM_WEBHOOK = "job_forwarded_from_webhook"
    APPLICATION_FORWARDED_FROM_WEBHOOK = "application_forwarded_from_webhook"


class MixpanelDomainEvents(MixpanelService):
    def user_created(self, user_id: str, first_name: str, last_name: str, email: str):
        properties = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
        }
        self.track(user_id, None, EventName.USER_CREATED, properties)
        self.update_user_profile(user_id, properties)
    
    def company_created(self, user_id: str, company_id: str, company_name: str):
        properties = {
            "company_name": company_name,
        }
        self.track(user_id, company_id, EventName.COMPANY_CREATED, properties)
        self.update_company_profile(company_id, properties)
    
    def recruiter_is_invited_to_company(self, inviting_user_id: str, company_id: str, role: str, invitation_id: str):
        properties = {
            "role": role,
            "invitation_id": invitation_id,
        }
        self.track(inviting_user_id, company_id, EventName.RECRUITER_IS_INVITED_TO_COMPANY, properties)
    
    def recruiter_invitation_is_accepted(self, accepting_user_id: str, company_id: str, role: str, invitation_id: str):
        properties = {
            "role": role,
            "invitation_id": invitation_id,
        }
        self.track(accepting_user_id, company_id, EventName.RECRUITER_INVITATION_IS_ACCEPTED, properties)
    
    def job_description_is_generated(self, user_id: str, company_id: str, generation_type: str):
        properties = {
            "generation_type": generation_type,
        }
        self.track(user_id, company_id, EventName.JOB_DESCRIPTION_IS_GENERATED, properties)
    
    def resume_is_scanned(self, user_id: str, company_id: str | None, application_id: str):
        properties = {
            "application_id": application_id,
        }
        self.track(user_id, company_id, EventName.RESUME_IS_SCANNED, properties)

    def application_is_submitted_and_enriched(self, user_id: str, company_id: str, job_id: str, application_id: str):
        properties = {
            "job_id": job_id,
            "application_id": application_id,
        }
        self.track(user_id, company_id, EventName.APPLICATION_IS_SUBMITTED_AND_ENRICHED, properties)

    def job_created_from_portal(self, user_id: str, company_id: str, job_id: str, position_title: str | None):
        properties = {
            "job_id": job_id,
            "position_title": position_title,
        }
        self.track(user_id, company_id, EventName.JOB_CREATED_FROM_PORTAL, properties)

    # TODO we don't have this feature yet... add a description as the body text and generate job from that would be cool
    # def job_created_from_email_ingress(self, user_id: str, company_id: str):
    #     properties = {}
    #     self.track(user_id, company_id, EventName.JOB_CREATED_FROM_EMAIL_INGRESS, properties)
    
    def job_created_from_api_webhook_ingress(self, user_id: str, company_id: str, external_reference_code: str | None):
        properties = {
            "external_reference_code": external_reference_code,
        }
        self.track(user_id, company_id, EventName.JOB_CREATED_FROM_API_WEBHOOK_INGRESS, properties)
    
    def application_created_from_api_webhook_ingress(self, user_id: str, company_id: str, external_job_reference_code: str | None, application_id: str):
        properties = {
            "external_job_reference_code": external_job_reference_code,
            "application_id": application_id,
        }
        self.track(user_id, company_id, EventName.APPLICATION_CREATED_FROM_API_WEBHOOK_INGRESS, properties)

    def application_created_from_portal(self, user_id: str, company_id: str, job_id: str, application_id: str, creation_type: Literal["csv", "pdf", "manual_form"]):
        properties = {
            "job_id": job_id,
            "application_id": application_id,
            "creation_type": creation_type,
        }
        self.track(user_id, company_id, EventName.APPLICATION_CREATED_FROM_PORTAL, properties)

    def application_created_from_email_ingress(self, user_id: str, company_id: str, job_id: str, application_id: str):
        properties = {
            "job_id": job_id,
            "application_id": application_id,
        }
        self.track(user_id, company_id, EventName.APPLICATION_CREATED_FROM_EMAIL_INGRESS, properties)
    
    def application_is_shortlisted(self, user_id: str, company_id: str, job_id: str, application_id: str):
        properties = {
            "job_id": job_id,
            "application_id": application_id,
        }
        self.track(user_id, company_id, EventName.APPLICATION_IS_SHORTLISTED, properties)
    
    def application_is_viewed(self, user_id: str, company_id: str, job_id: str | None, application_id: str):
        properties = {
            "job_id": job_id,
            "application_id": application_id,
        }
        self.track(user_id, company_id, EventName.APPLICATION_IS_VIEWED, properties)
    
    def application_is_deleted(self, user_id: str, company_id: str, job_id: str, application_id: str):
        properties = {
            "job_id": job_id,
            "application_id": application_id,
        }
        self.track(user_id, company_id, EventName.APPLICATION_IS_DELETED, properties)
    
    def application_status_is_updated(self, user_id: str, company_id: str, job_id: str, application_id: str, new_status: str):
        properties = {
            "job_id": job_id,
            "application_id": application_id,
            "new_status": new_status,
        }
        self.track(user_id, company_id, EventName.APPLICATION_STATUS_IS_UPDATED, properties)

    def job_forwarded_from_webhook(self, company_id: str, job_id: str):
        properties = {
            "job_id": job_id,
        }
        self.track("webhook_forwarding", company_id, EventName.JOB_FORWARDED_FROM_WEBHOOK, properties)
    
    def application_forwarded_from_webhook(self, company_id: str, job_id: str, application_id: str):
        properties = {
            "job_id": job_id,
            "application_id": application_id,
        }
        self.track("webhook_forwarding", company_id, EventName.APPLICATION_FORWARDED_FROM_WEBHOOK, properties)
