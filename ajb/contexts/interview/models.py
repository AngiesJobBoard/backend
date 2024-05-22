from enum import Enum
from typing import List
from pydantic import BaseModel, Field


class Subsection(BaseModel):
    """Class representing a related subsection containing questions."""

    title: str = Field(..., description="Title of the subsection")
    questions: List[str] = Field(
        ...,
        description="List of questions in the subsection",
    )


class SectionType(str, Enum):
    """Enumeration representing the types of sections in the question outline."""

    TECH_SKILLS_AND_EXPERIENCE = "Technical Skills and Experience"
    PROJECT_AND_PROBLEM_SOLVING_SKILLS = "Project and Problem-Solving Skills"
    COLLABORATION_AND_COMMUNICATION = "Collaboration and Communication"
    ACHIEVEMENTS_AND_IMPACT = "Achievements and Impact"
    EDUCATION_AND_CONTINUOUS_LEARNING = "Education and Continuous Learning"


class Section(BaseModel):
    """Class representing a main section containing subsections."""

    title: SectionType = Field(..., description="Title of the main section")
    subsections: List[Subsection] = Field(
        default_factory=list,
        description="List of subsections in the main section",
    )


class QuestionDocument(BaseModel):
    """Class representing the entire question outline structure for an interview."""

    question_outline: List[Section] = Field(
        default_factory=list,
        description="List of main sections in the document",
    )
