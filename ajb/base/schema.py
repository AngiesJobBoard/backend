"""
Contains the database entities such as collections, views, and everything else that will be stored in the database.

It is used to identify the collections and views that are being used for all operations as well
as create them when running a migration or creating a new database.
"""

from enum import Enum
from pydantic import BaseModel


class Collection(str, Enum):
    """
    A Collection is like a database table, it holds information about a specific entity
    """

    # Users (or candidates )

    USERS = "users"
    USER_SAVED_COMPANIES = "user_saved_companies"
    USER_SAVED_JOBS = "user_saved_jobs"
    USER_ACTIONS = "user_actions"
    COVER_LETTERS = "cover_letters"
    RESUMES = "resumes"
    USER_NOTIFICATIONS = "user_notifications"

    # Companies

    COMPANIES = "companies"
    COMPANY_RECRUITERS = "company_recruiters"
    COMPANY_ACTIONS = "company_actions"
    COMPANY_SAVES_CANDIDATES = "company_saves_candidates"
    RECRUITER_INVITATIONS = "recruiter_invitations"
    JOBS = "jobs"
    JOB_TEMPLATES = "job_templates"
    COMPANY_OFFICES = "company_offices"
    APPLICATIONS = "applications"
    COMPANY_NOTIFICATIONS = "company_notifications"

    # System
    SCHEDULED_EVENTS = "scheduled_events"

    # Admin entities
    ADMIN_USERS = "admin_users"
    ADMIN_JOB_APPROVALS = "admin_job_approvals"
    ADMIN_ACCESS = "admin_access"

    # Static content
    STATIC_DATA = "static_data"


class View(str, Enum):
    """
    A View can be one or multiple collections that are optimized for searching.

    To create a view you must define how this view is built by referencing it
    in the VIEW_DEFINITIONS dictionary below
    """

    JOBS_VIEW = "jobs_view"
    USERS_VIEW = "users_view"
    COMPANIES_VIEW = "companies_view"
    APPLICANTS_VIEW = "applicants_view"
    STATIC_DATA_VIEW = "static_data_view"


class Analyzer(str, Enum):
    IDENTITY = "identity"


class ViewLink(BaseModel):
    analyzers: list[Analyzer]
    fields: dict[str, dict[str, str]]
    includeAllFields: bool
    storeValues: str
    trackListPositions: bool


class ViewProperties(BaseModel):
    name: str
    type: str = "arangosearch"
    links: dict[Collection, ViewLink]


VIEW_DEFINITIONS: dict[View, ViewProperties] = {
    View.JOBS_VIEW: ViewProperties(
        name=View.JOBS_VIEW.value,
        links={
            Collection.JOBS: ViewLink(
                analyzers=[Analyzer.IDENTITY],
                fields={},
                includeAllFields=True,
                storeValues="none",
                trackListPositions=False,
            ),
        },
    ),
    View.USERS_VIEW: ViewProperties(
        name=View.USERS_VIEW.value,
        links={
            Collection.USERS: ViewLink(
                analyzers=[Analyzer.IDENTITY],
                fields={},
                includeAllFields=True,
                storeValues="none",
                trackListPositions=False,
            ),
        },
    ),
    View.COMPANIES_VIEW: ViewProperties(
        name=View.COMPANIES_VIEW.value,
        links={
            Collection.COMPANIES: ViewLink(
                analyzers=[Analyzer.IDENTITY],
                fields={},
                includeAllFields=True,
                storeValues="none",
                trackListPositions=False,
            ),
        },
    ),
    View.APPLICANTS_VIEW: ViewProperties(
        name=View.APPLICANTS_VIEW.value,
        links={
            Collection.APPLICATIONS: ViewLink(
                analyzers=[Analyzer.IDENTITY],
                fields={},
                includeAllFields=True,
                storeValues="none",
                trackListPositions=False,
            ),
        },
    ),
    View.STATIC_DATA_VIEW: ViewProperties(
        name=View.STATIC_DATA_VIEW.value,
        links={
            Collection.STATIC_DATA: ViewLink(
                analyzers=[Analyzer.IDENTITY],
                fields={},
                includeAllFields=True,
                storeValues="none",
                trackListPositions=False,
            ),
        },
    ),
}
