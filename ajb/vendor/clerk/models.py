from enum import Enum
from pydantic import BaseModel, Field


class ClerkWebhookEvent(BaseModel):
    data: dict
    object: str
    type: Enum


class ClerkBaseModel(BaseModel):
    id: str
    object: str


class ClerkUserWebhookType(str, Enum):
    user_created = "user.created"


class ClerkUserWebhookEvent(ClerkWebhookEvent):
    type: ClerkUserWebhookType


class ClerkUserEmailAddresses(ClerkBaseModel):
    email_address: str
    linked_to: list = Field(default_factory=list)
    verification: dict = Field(default_factory=dict)


class ClertkUserPhoneNumbers(ClerkBaseModel):
    phone_number: str
    linked_to: list = Field(default_factory=list)
    verification: dict = Field(default_factory=dict)


class ClerkUser(ClerkBaseModel):
    created_at: int
    primary_email_address_id: str
    email_addresses: list[ClerkUserEmailAddresses]
    phone_numbers: list[ClertkUserPhoneNumbers]
    first_name: str
    last_name: str
    external_id: str | None = None
    image_url: str | None = None
    email: str = ""
    phone_number: str | None = None
    private_metadata: dict = Field(default_factory=dict)

    def __init__(self, **data):
        super().__init__(**data)
        self.email = next(
            (
                email_address.email_address
                for email_address in self.email_addresses
                if email_address.id == self.primary_email_address_id
            ),
            "",
        )
        self.phone_number = next(
            (
                phone_number.phone_number
                for phone_number in self.phone_numbers
                if phone_number.linked_to == [self.primary_email_address_id]
            ),
            None,
        )


class SimpleClerkCreateUser(BaseModel):
    first_name: str
    last_name: str
    email_address: str
    password: str
    skip_password_checks: bool = False
    skip_password_requirement: bool = False


class ClerkCreateUser(BaseModel):
    first_name: str
    last_name: str
    email_address: list[str]
    phone_number: list[str] = Field(default_factory=list)
    password: str
    skip_password_checks: bool = False
    skip_password_requirement: bool = False
    public_metadata: dict = Field(default_factory=dict)
    private_metadata: dict = Field(default_factory=dict)
    unsafe_metadata: dict = Field(default_factory=dict)


class SignInToken(BaseModel):
    object: str
    id: str
    status: str
    user_id: str
    token: str
    url: str
    created_at: int
    updated_at: int
