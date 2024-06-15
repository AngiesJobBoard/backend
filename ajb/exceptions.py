from fastapi import HTTPException


class EntityNotFound(HTTPException):
    def __init__(
        self,
        collection: str,
        entity_id: str | None = None,
        attribute: str | None = None,
        value: str | None = None,
    ):
        detail_string = collection
        if entity_id:
            detail_string += f" with id {entity_id}"
        if attribute:
            detail_string += f" with {attribute} equal to {value}"
        detail_string += " not found"
        super().__init__(
            status_code=404,
            detail=detail_string,
        )


class MultipleEntitiesReturned(HTTPException):
    def __init__(self, entity_name: str):
        detail_string = entity_name
        detail_string += " has multiple entries"
        super().__init__(
            status_code=404,
            detail=detail_string,
        )


class FailedToCreate(Exception):
    def __init__(self, collection: str, overridden_id: str | None):
        self.message = f"Failed to create {collection}"
        if overridden_id:
            self.message += f" with id {overridden_id}"
        super().__init__(self.message)


class InvalidTokenException(Exception):
    def __init__(self, message="Invalid token"):
        self.message = message
        super().__init__(self.message)


class ExpiredTokenException(Exception):
    def __init__(self, message="Expired token"):
        self.message = message
        super().__init__(self.message)


class AdminCreateUserException(Exception):
    def __init__(self, message="Failed to create user"):
        self.message = message
        super().__init__(self.message)


class CompanyCreateException(Exception):
    def __init__(self, message="Failed to create company"):
        self.message = message
        super().__init__(self.message)


class GenericPermissionError(Exception):
    def __init__(self, message="Permission denied"):
        self.message = message
        super().__init__(self.message)


class RecruiterCreateException(Exception):
    def __init__(self, message="Failed to create recruiter"):
        self.message = message
        super().__init__(self.message)


class GenericTypeError(Exception):
    def __init__(self, message="Object type mismatch"):
        self.message = message
        super().__init__(self.message)


class FailedToPostJobException(Exception):
    def __init__(self, message="Failed to post job"):
        self.message = message
        super().__init__(self.message)


class FailedToUpdateJobException(Exception):
    def __init__(self, message="Failed to update job"):
        self.message = message
        super().__init__(self.message)


class FailedToCreateApplication(Exception):
    def __init__(self, message="Failed to create application"):
        self.message = message
        super().__init__(self.message)


class MissingJobFieldsException(Exception):
    def __init__(self, message="Missing job fields", fields: list[str] = []):
        self.message = message
        if fields:
            self.message += f": {fields}"
        super().__init__(self.message)


class RequestScopeWithoutCompanyException(Exception):
    def __init__(self, message="Request scope without company being used"):
        self.message = message
        super().__init__(self.message)


class RepositoryNotProvided(Exception):
    def __init__(self, repository_name: str):
        self.message = f"{repository_name} not provided"
        super().__init__(self.message)


class TierLimitHitException(Exception):
    def __init__(self, message="Tier limit hit"):
        self.message = message
        super().__init__(self.message)
