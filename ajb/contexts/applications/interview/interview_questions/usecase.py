from ajb.contexts.applications.interview.interview_questions.models import (
    InterviewQuestions,
)
from ajb.contexts.applications.interview.interview_questions.ai_interview_questions import (
    AIJobInterviewQuestions,
)
from ajb.vendor.openai.repository import OpenAIRepository
from ajb.base import BaseUseCase, Collection, RequestScope


class InterviewQuestionUsecase(BaseUseCase):

    def __init__(
        self, request_scope: RequestScope, openai: OpenAIRepository | None = None
    ) -> None:
        self.ai_job_interview_questions = AIJobInterviewQuestions(openai)
        self.request_scope = request_scope

    def generate_job_interview_questions(
        self, job_id: str, application_id: str
    ) -> InterviewQuestions:
        interview_questions_repo = self.get_repository(
            Collection.INTERVIEW_QUESTIONS, self.request_scope, application_id
        )
        application = self.get_object(Collection.APPLICATIONS, application_id)
        job = self.get_object(Collection.JOBS, job_id)
        interview_questions_to_create = (
            self.ai_job_interview_questions.generate_interview_questions(
                job=job, application=application
            )
        )
        return interview_questions_repo.set_sub_entity(interview_questions_to_create)

    def ai_generate_interview_questions(
        self, resume: str, job_post: str
    ) -> InterviewQuestions:
        system_prompt = """
        You are a perfect at assisting an interviewer with generating insightful questions. Using the given resume and job post listing, generate a suite of tailored interview questions that assess the interviewee's qualifications, experiences, and skills relevant to the job. Ensure the questions are comprehensive and cover different aspects.
        """

        prompt = f"""
        Generate a suite of tailored interview questions based on the provided resume and job post.

        **Resume:**
        {resume}

        **Job Post Listing:**
        {job_post}

        Use the resume and job post to generate more specific and relevant questions, ensuring they address the key points mentioned in both documents.
        """

        response = self.openai.structured_prompt(
            prompt=prompt,
            response_model=InterviewQuestions,
            system_prompt=system_prompt,
            max_tokens=4096,
        )

        return response


# if __name__ == "__main__":
#     resume_text = """EXPERIENCE
# Software Engineer - Matcher Jan 2024 - Present
# ● CollaboratedwithMatcher'smaindeveloperbuildingoutdetailinterfaces,featuringcandidatenavigation,
# proprietary fit analysis, and status tracking to streamline recruiter workflows.
# ● Engineeredanadminportaltofacilitateaccountmodificationsforcustomersupport,increasingoperational
# efficiency and security by reducing direct database interactions.
# Business Process Automation Engineer - Spiffy May 2023 - Jan 2024
# ● Engineeredandoptimizedabackendframeworktoautomatetasks,notablystreamliningordercreationfromemail
# reception and invoice generation via UI automation, resulting in a 30% reduction in manual processing time and a
# 25% increase in operational efficiency.
# ● Teamedwithcustomersupportandfinancetooptimizebusinessworkflows,involvingthecreationofautomated
# solutions for data processing and management.
# ● Collaboratedwitha5personhardwareteamtobuildanapplicationtomakeactionabledecisionsforupper
# management based on insights given from proprietary data.
# Software Engineer - Qlair May 2022 - May 2023
# ● Redesignedtheserver-sidearchitectureandimplementedAWScloud-basedbackendsolutions,resultingina50%
# increase in development speed.
# ● Reducederroroccurrencesby15%andenhancedsystemreliabilityby10%throughdiagnosing,debugging,and
# refining tested software.
# ● Conductedendtoendtestsandunitteststoevaluatecodecoverage.
# ● Enhancedthemainfrontendapplicationwithvariouswidgetgaugesandimprovedadminportalefficiency
# resulting in a 20% decrease in support ticket time.
# Software Engineer - Momentum Learning Jan 2022 - May 2022
# ● Dedicated16-weekimmersivefull-stackcodingbootcampwithemphasisinPython,Javascriptanddeployingweb
# applications in Django and React.
# ● Built20+applicationsusingHTML,CSS,Javascript,Python,DjangoandReact.
# ● Ledaremotefourpersonteaminanagileenvironmenttoproduceanapplicationthattrackedvolunteerhours,
# charitable donations, and provided the user with useful insights on their contributions.
# PROJECTS
# ● Brogrammer:AnAI-poweredcodereviewCLItoolusingtheGPTmodels.Itofferscustomizablefeedback options, including file selection and git diff comparisons.
# ● Gym-Dot:Aprojecttolearnthebasicsofcreatingamodernfrontendpullinginformationfrommultipleexternal API's.
# ● Portfolio:tedfulk.com TECHNICAL SKILLS
# ● Languages: Python, Javascript, TypeScript, Svelte, Bash, Fish
# ● Frameworks: React, Svelte Kit, Nextjs, Django, SQLAlchemy, FastAPI
# ● Version control: Git, GitHub, Bitbucket
# ● Cloud: AWS, Heroku, Netlify, Google Cloud
# ● Database: DynamoDB, PostgreSQL, SQL, EdgeDB, Arrango, Melisearch
# ● Process: Agile, Scrum, Jira, Trello, Slack, Zoom, Teams
# EDUCATION
# Momentum Learning
# Full Stack Software Engineer Programming
# Purdue University
# Bachelor of Movement and Sport Science
# May 2022
# Durham, NC
# Jul 2015
# West Lafayette, IN"""

#     job_posting_text = """Job Posting: Backend Developer for AI Applications
# Company Overview:
# We are an innovative tech company at the forefront of artificial intelligence and machine learning solutions. Our mission is to transform industries through cutting-edge AI applications that drive efficiency, innovation, and excellence. We are looking for a talented and passionate Backend Developer to join our dynamic team and help build state-of-the-art AI applications.

# Position: Backend Developer (AI Applications)
# Location: Remote/On-site (depending on candidate preference)

# Type: Full-time

# Salary: Competitive, based on experience

# Job Description:
# As a Backend Developer for AI Applications, you will be responsible for designing, implementing, and maintaining the server-side logic and architecture that powers our AI-driven solutions. You will work closely with our data scientists, frontend developers, and product managers to develop robust, scalable, and high-performance backend systems.

# Key Responsibilities:
# Design and Development: Design, build, and maintain scalable backend architectures and services to support AI applications.
# API Development: Develop RESTful and GraphQL APIs to enable seamless integration with frontend applications and other services.
# Database Management: Design and manage relational and NoSQL databases, ensuring optimal performance and reliability.
# Data Processing: Implement data pipelines and ETL processes to facilitate the ingestion, transformation, and storage of large datasets.
# Security: Ensure data and application security, including authentication, authorization, and data encryption.
# Testing and Debugging: Conduct rigorous testing and debugging to ensure the reliability and performance of backend systems.
# Collaboration: Collaborate with cross-functional teams, including data scientists, frontend developers, and product managers, to deliver end-to-end AI solutions.
# Documentation: Create and maintain comprehensive documentation for backend systems and processes.
# Requirements:
# Education: Bachelor's or Master's degree in Computer Science, Engineering, or a related field.
# Experience:
# 3+ years of experience in backend development, preferably in AI or machine learning environments.
# Proven experience with programming languages such as Python, Java, or Node.js.
# Technical Skills:
# Strong understanding of RESTful and GraphQL API design and implementation.
# Proficiency with relational databases (e.g., PostgreSQL, MySQL) and NoSQL databases (e.g., MongoDB, Cassandra).
# Experience with cloud platforms (e.g., AWS, Google Cloud, Azure) and containerization technologies (e.g., Docker, Kubernetes).
# Familiarity with data processing frameworks and tools (e.g., Apache Kafka, Apache Spark).
# Knowledge of machine learning frameworks and libraries (e.g., TensorFlow, PyTorch) is a plus.
# Soft Skills:
# Excellent problem-solving skills and attention to detail.
# Strong communication skills and the ability to work collaboratively in a team environment.
# Ability to manage multiple tasks and prioritize effectively.
# Preferred Qualifications:
# Experience with microservices architecture and serverless computing.
# Familiarity with DevOps practices and tools (e.g., CI/CD pipelines, Jenkins).
# Knowledge of AI/ML lifecycle management tools and platforms.
# What We Offer:
# Innovative Work Environment: Be part of a team that values innovation, creativity, and collaboration.
# Career Growth: Opportunities for professional development and career advancement.
# Competitive Benefits: Comprehensive health, dental, and vision insurance, retirement plans, and more.
# Flexible Work Arrangements: Options for remote work and flexible scheduling."""

#     usecase = InterviewQuestionUsecase()
#     usecase.generate_interview_questions(resume_text, job_posting_text)

# {
#     "question_outline": [
#         {
#             "title": "Technical Skills and Experience",
#             "subsections": [
#                 {
#                     "title": "Programming Languages and Frameworks",
#                     "questions": [
#                         "Can you share your experience with Python, particularly in backend development for AI applications?",
#                         "Describe a project where you utilized JavaScript or TypeScript for backend development. What were the challenges and how did you overcome them?",
#                         "How have you used Django or FastAPI in your previous roles? Can you provide specific examples of applications you developed using these frameworks?",
#                     ],
#                 },
#                 {
#                     "title": "Cloud Platforms and Database Management",
#                     "questions": [
#                         "What is your experience with AWS, and can you provide examples of backend solutions you have implemented using this platform?",
#                         "Can you discuss your experience with both relational databases like PostgreSQL and NoSQL databases such as DynamoDB? How did you ensure their performance and reliability?",
#                         "Describe a situation where you designed and managed a database for a large dataset. What strategies did you use for data ingestion, transformation, and storage?",
#                     ],
#                 },
#                 {
#                     "title": "API Development",
#                     "questions": [
#                         "Can you give examples of RESTful or GraphQL APIs that you have developed? How did they integrate with frontend applications and other services?",
#                         "Describe a challenging API development project you worked on. What were the key challenges and how did you address them?",
#                     ],
#                 },
#                 {
#                     "title": "Security",
#                     "questions": [
#                         "What strategies do you employ to ensure data and application security, specifically regarding authentication, authorization, and encryption?",
#                         "Can you provide an example from your past experience where you implemented security measures to protect sensitive data?",
#                     ],
#                 },
#                 {
#                     "title": "Testing and Debugging",
#                     "questions": [
#                         "How do you approach testing and debugging to ensure the reliability and performance of backend systems?",
#                         "Can you describe a situation where your testing and debugging significantly improved the system's reliability?",
#                     ],
#                 },
#             ],
#         },
#         {
#             "title": "Collaboration and Communication",
#             "subsections": [
#                 {
#                     "title": "Team Collaboration",
#                     "questions": [
#                         "Describe a project where you closely collaborated with data scientists, frontend developers, and product managers. What was your role and how did you ensure effective communication and collaboration?",
#                         "How have you applied Agile or Scrum methodologies in your past roles? Can you share an example of how these methodologies improved project outcomes?",
#                     ],
#                 },
#                 {
#                     "title": "Problem-solving and Prioritization",
#                     "questions": [
#                         "Can you provide an example of a complex problem you encountered in backend development and how you resolved it?",
#                         "How do you manage and prioritize multiple tasks in a dynamic work environment?",
#                     ],
#                 },
#             ],
#         },
#         {
#             "title": "Achievements and Impact",
#             "subsections": [
#                 {
#                     "title": "Project Insights",
#                     "questions": [
#                         "Can you elaborate on the AI-powered code review CLI tool 'Brogrammer' you developed? What technologies did you use and what were the key features?",
#                         "What were the primary objectives and results of the 'Gym-Dot' project? How did you ensure the frontend effectively pulled information from multiple external APIs?",
#                         "Your portfolio includes multiple applications; can you highlight one that you are particularly proud of and explain why?",
#                     ],
#                 },
#                 {
#                     "title": "Innovative Work and Continuous Learning",
#                     "questions": [
#                         "How do you stay updated with the latest advancements in AI and backend development?",
#                         "Can you describe a time when you introduced an innovative solution or technology to a project? What was the impact?",
#                     ],
#                 },
#             ],
#         },
#         {
#             "title": "Project and Problem-Solving Skills",
#             "subsections": [
#                 {
#                     "title": "Cultural Fit and Motivation",
#                     "questions": [
#                         "What excites you most about the opportunity to work with our team on AI applications?",
#                         "How do you see yourself contributing to our mission of transforming industries through AI?",
#                     ],
#                 },
#                 {
#                     "title": "Career Goals",
#                     "questions": [
#                         "What are your long-term career goals and how does this position align with them?",
#                         "How do you envision growing within our company?",
#                     ],
#                 },
#             ],
#         },
#     ]
# }
