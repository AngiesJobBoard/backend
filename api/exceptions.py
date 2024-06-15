from fastapi import HTTPException


class Forbidden(HTTPException):
    def __init__(self, detail: str | None = None):
        super().__init__(status_code=403, detail=detail or "Forbidden")


class InvalidToken(HTTPException):
    def __init__(self, detail: str | None = None):
        super().__init__(status_code=401, detail=detail or "Invalid token")


class GenericHTTPException(HTTPException):
    def __init__(self, status_code: int = 400, detail: str | None = None):
        super().__init__(status_code=status_code, detail=detail or "Unknown error")


class NotFound(HTTPException):
    def __init__(self, detail: str | None = None):
        super().__init__(status_code=404, detail=detail or "Not found")


class TierLimitHTTPException(HTTPException):
    def __init__(self, detail: str | None = None):
        super().__init__(status_code=402, detail=detail or "Tier limit reached")
