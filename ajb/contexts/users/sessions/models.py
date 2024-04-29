from pydantic import BaseModel


class SessionData(BaseModel):
    """Should also contain expiry information or other..."""

    id: str
    actor: dict | None = None
    public_meta: dict | None = None
