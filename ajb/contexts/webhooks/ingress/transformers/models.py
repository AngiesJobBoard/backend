from pydantic import BaseModel, Field


# class FieldTransformation(BaseModel):
#     target_field: str
#     conversion_type: str | None = None
#     default_value: Optional[Any] = None
#     required: Optional[bool] = False
#     validations: Optional[Dict[str, Any]] = None


# class SourceConfig(BaseModel):
#     source_name: str
#     field_mappings: Dict[str, FieldTransformation]


# class TransformationConfig(BaseModel):
#     transformations: List[SourceConfig]


# # Example Usage:
# transformation_example = TransformationConfig(
#     transformations=[
#         SourceConfig(
#             source_name="ExampleSource",
#             field_mappings={
#                 "source_field_name": FieldTransformation(
#                     target_field="target_field_name",
#                     conversion_type="string",
#                     default_value="N/A",
#                     required=True,
#                     validations={"max_length": 100},
#                 )
#             },
#         )
#     ]
# )


"""
Some examples?

{
"applicationId": "123456",
  "applicantDetails": {
    "firstName": "Jane",
    "lastName": "Doe",
    "email": "jane.doe@example.com",
    "phone": "+1234567890",
    "address": {
      "street": "123 Main St",
      "city": "Anytown",
      "state": "Anystate",
      "country": "Country",
      "zipCode": "12345"
    },
    "linkedinProfile": "https://www.linkedin.com/in/janedoe",
    "portfolioURL": "http://janedoeportfolio.com"
  },
  "qualifications": {
    "education": [
      {
        "degree": "Bachelor of Science in Computer Science",
        "institution": "University of Technology",
        "yearCompleted": 2020
      },
      {
        "degree": "Master of Science in Software Engineering",
        "institution": "Tech Advanced Institute",
        "yearCompleted": 2022
      }
    ],
    "certifications": [
      {
        "name": "Certified Scrum Master",
        "issuingOrganization": "Scrum Alliance",
        "dateObtained": "2023-01-15"
      },
      {
        "name": "AWS Certified Solutions Architect",
        "issuingOrganization": "Amazon Web Services",
        "dateObtained": "2023-03-22"
      }
    ],
    "skills": ["Java", "Python", "AWS", "Docker", "Kubernetes", "Agile Methodologies", "Scrum"],
    "languages": ["English (Fluent)", "Spanish (Conversational)"],
    "workExperience": [
      {
        "company": "Tech Innovations Inc.",
        "title": "Software Engineer",
        "startDate": "2022-05-01",
        "endDate": "Present",
        "responsibilities": [
          "Developed and maintained scalable web applications",
          "Led the migration of on-premise infrastructure to AWS",
          "Implemented CI/CD pipelines reducing deployment time by 50%"
        ]
      },
      {
        "company": "Global Tech Solutions",
        "title": "Junior Software Developer",
        "startDate": "2020-06-01",
        "endDate": "2022-04-30",
        "responsibilities": [
          "Assisted in the development of internal tools to improve workflow efficiency",
          "Participated in the full software development lifecycle (SDLC)",
          "Supported senior developers with coding and debugging"
        ]
      }
    ]
  },
}

"""
