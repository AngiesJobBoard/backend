from pydantic import BaseModel


class BaseEmailData(BaseModel):
    platformName: str = "Angies Job Matcher"

    def to_str_dict(self):
        return {k: str(v) for k, v in self.model_dump().items()}
