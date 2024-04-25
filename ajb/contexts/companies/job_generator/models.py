from pydantic import BaseModel


class GenerateQualifications(BaseModel):
    selected_skills: list[str]
    recommended_skills: list[str]
    selected_licenses: list[str]
    recommended_licenses: list[str]
    selected_certifications: list[str]
    recommended_certifications: list[str]


class GenerateQuestions(BaseModel):
    selected_questions: list[str]
    recommended_questions: list[str]
