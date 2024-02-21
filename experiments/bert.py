from pydantic import BaseModel
from transformers import BertModel, BertTokenizer
import torch
from typing import List
import numpy as np


class BaseBertData(BaseModel):
    def to_bert_text(self):
        raise NotImplementedError


class JobData(BaseBertData):
    position_title: str
    description: str
    required_number_of_years_of_experience: int
    required_skills: List[str]
    required_licenses: List[str]
    required_certifications: List[str]
    required_spoken_languages: List[str]

    def to_bert_text(self):
        output_text = f"{self.position_title}"
        output_text += f" {', '.join(self.required_skills)}"
        output_text += f" {', '.join(self.required_licenses)}"
        output_text += f" {', '.join(self.required_certifications)}"
        output_text += f" {', '.join(self.required_spoken_languages)}"
        return output_text


class CandidateData(BaseBertData):
    last_job_title: str
    last_company_name: str
    total_years_experience: int
    skills: List[str]
    licenses: List[str]
    certifications: List[str]
    spoken_languages: List[str]

    def to_bert_text(self):
        output_text = f" {self.last_job_title}"
        output_text += f" {', '.join(self.skills)}"
        output_text += f" {', '.join(self.licenses)}"
        output_text += f" {', '.join(self.certifications)}"
        output_text += f" {', '.join(self.spoken_languages)}"
        return output_text


def model_to_vector(
    data: BaseBertData, model_name: str = "bert-base-uncased", vector_length: int = 256
) -> List[float]:
    tokenizer = BertTokenizer.from_pretrained(model_name)
    model = BertModel.from_pretrained(model_name)
    inputs = tokenizer(
        data.to_bert_text(),
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=512,
    )
    with torch.no_grad():
        outputs = model(**inputs)  # type: ignore
    embeddings = outputs.last_hidden_state
    sentence_embedding = torch.mean(embeddings, dim=1)
    reduced_vector = sentence_embedding[0][:vector_length].tolist()
    return reduced_vector


# Example usage
example_job = JobData(
    position_title="Software Engineer",
    description="We are looking for a software engineer to join our team",
    required_number_of_years_of_experience=5,
    required_skills=["Python", "Django", "React"],
    required_licenses=[],
    required_certifications=[],
    required_spoken_languages=["English"],
)

good_candidate_1 = CandidateData(
    last_job_title="Senior Software Developer",
    last_company_name="Amazon",
    total_years_experience=8,
    skills=["Java", "Spring Boot", "Microservices", "AWS"],
    licenses=[],
    certifications=["AWS Certified Solutions Architect"],
    spoken_languages=["English", "French"],
)

good_candidate_2 = CandidateData(
    last_job_title="Data Scientist",
    last_company_name="Facebook",
    total_years_experience=5,
    skills=["Python", "R", "Machine Learning", "Deep Learning", "SQL"],
    licenses=[],
    certifications=["Data Science Certificate"],
    spoken_languages=["English", "Spanish"],
)

good_candidate_3 = CandidateData(
    last_job_title="DevOps Engineer",
    last_company_name="Netflix",
    total_years_experience=7,
    skills=["Docker", "Kubernetes", "Ansible", "AWS", "Terraform"],
    licenses=[],
    certifications=["Certified Kubernetes Administrator"],
    spoken_languages=["English"],
)

good_candidate_4 = CandidateData(
    last_job_title="Full Stack Developer",
    last_company_name="Microsoft",
    total_years_experience=6,
    skills=["JavaScript", "React", "Node.js", "Azure", "SQL"],
    licenses=[],
    certifications=["Microsoft Certified: Azure Developer Associate"],
    spoken_languages=["English", "Mandarin"],
)

good_candidate_5 = CandidateData(
    last_job_title="Product Manager",
    last_company_name="Apple",
    total_years_experience=9,
    skills=["Product Management", "Agile Methodologies", "User Experience"],
    licenses=[],
    certifications=["Certified ScrumMaster"],
    spoken_languages=["English", "German"],
)

bad_candidate_1 = CandidateData(
    last_job_title="Office Assistant",
    last_company_name="Small Local Business",
    total_years_experience=2,
    skills=["Word Processing", "Spreadsheets"],
    licenses=[],
    certifications=[],
    spoken_languages=["English"],
)

bad_candidate_2 = CandidateData(
    last_job_title="Retail Sales Associate",
    last_company_name="Generic Retail Store",
    total_years_experience=1,
    skills=["Customer Service", "Cash Handling"],
    licenses=[],
    certifications=[],
    spoken_languages=["English"],
)

bad_candidate_3 = CandidateData(
    last_job_title="Waiter",
    last_company_name="Local Restaurant",
    total_years_experience=3,
    skills=["Food Service", "POS Systems"],
    licenses=[],
    certifications=["Food Handler Certification"],
    spoken_languages=["English", "Spanish"],
)

bad_candidate_4 = CandidateData(
    last_job_title="Housekeeper",
    last_company_name="Hotel Chain",
    total_years_experience=4,
    skills=["Cleaning", "Time Management"],
    licenses=[],
    certifications=[],
    spoken_languages=["Spanish"],
)

bad_candidate_5 = CandidateData(
    last_job_title="Landscaper",
    last_company_name="Landscaping Company",
    total_years_experience=2,
    skills=["Gardening", "Equipment Operation"],
    licenses=["Commercial Driver’s License"],
    certifications=[],
    spoken_languages=["English"],
)


all_candidate_vectors = [
    model_to_vector(good_candidate_1),
    model_to_vector(good_candidate_2),
    model_to_vector(good_candidate_3),
    model_to_vector(good_candidate_4),
    model_to_vector(good_candidate_5),
    model_to_vector(bad_candidate_1),
    model_to_vector(bad_candidate_2),
    model_to_vector(bad_candidate_3),
    model_to_vector(bad_candidate_4),
    model_to_vector(bad_candidate_5),
]
job_vector = model_to_vector(example_job)


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    # Convert lists to numpy arrays
    vec1 = np.array(vec1)  # type: ignore
    vec2 = np.array(vec2)  # type: ignore

    # Calculate the dot product of the vectors
    dot_product = np.dot(vec1, vec2)

    # Calculate the norm (magnitude) of each vector
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)

    # Calculate the cosine similarity
    similarity = dot_product / (norm_vec1 * norm_vec2)

    return similarity


vector_distances = [
    cosine_similarity(job_vector, candidate_vector)
    for candidate_vector in all_candidate_vectors
]

import matplotlib.pyplot as plt


def plot_similarity(similarities: List[float], title: str):
    plt.bar(range(len(similarities)), similarities, color="skyblue")
    plt.title(title)
    plt.xlabel("Candidate")
    plt.ylabel("Similarity")
    plt.show()


plot_similarity(vector_distances, "Cosine Similarity of Candidates to Job")
