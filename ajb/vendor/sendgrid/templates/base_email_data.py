from datetime import datetime
from enum import Enum
from pydantic import BaseModel

from ajb.config.settings import SETTINGS


class SendgridTemplateId(str, Enum):
    RECRUITER_INVITATION = "d-8f3c659a700f44d9a1757ee449768250"
    NEWLY_CREATED_COMPANY = "d-bc1bfbf013b3433ea435ce9558893e19"
    NEWLY_CREATED_USER = "d-3abb19316ebd45ddafd02af63cdaff7b"


class BaseEmailData(BaseModel):
    platformName: str = SETTINGS.APP_NAME
    supportEmail: str = SETTINGS.SUPPORT_EMAIL
    currentYear: int = datetime.now().year
    templateId: SendgridTemplateId

    def to_str_dict(self):
        return {k: str(v) for k, v in self.model_dump(exclude={"templateId"}).items()}
