"""
These models are the foundation of our boosting mechanism.

All boosts are the same cost and are additive for a single job posting.

The timeliness or effectiveness of a boost is dependent on the demand for that type of boost.

We will also adjust this based on the performance of the boost.

So, the effectiveness of a job boost should be the following:

cost of boost = 1 unit
effectiveness of boost is f(demand, performance)

As demand and performance increase, the effectiveness of the boost decreases.

The performance of a boost is the number of clicks on the boost divided by the number of times the boost was shown.

The demand of a boost is the number of times the boost was shown divided by the number of times the boost was available.

The effectiveness of a boost is the number of clicks on the boost divided by the number of times the boost was available.

The cost of a boost is 1 unit.

"""

from enum import Enum


class BoostType(str, Enum):
    general_keyword_search = "general_keyword_search"  # Based on raw text in search bar
    location = "location"  # Based on proximity to location (like increase relevancy in a radius around job location)
    industry = "industry"  # Increase relevanccy when a user filters by industry
    company = "company"  # Increase relevancy when a user filters by company (could be a competitor)

    anonymous_user_home_page = "anonymous_user_home_page"  # Increase relevancy of appearing on home page for anonymous users

    job_title_search = (
        "job_title_search"  # Increase relevancy when a user searches for a job title
    )
    job_category = (
        "job_category"  # Increase relevancy when a user filters by job category
    )
    job_experience_level = "job_experience_level"  # Increase relevancy when a user filters by experience level
    job_education_level = "job_education_level"  # Increase relevancy when a user filters by education level
    job_salary = "job_salary"  # Increase relevancy when a user filters by salary
    resume_based_search = "resume_based_search"  # Increase relevancy when a user searches based on their experience
    recommended_jobs = (
        "recommended_jobs"  # Increase relevancy when a user is recommended a job
    )

    user_education_level = "user_education_level"  # Increase relevancy when a user has a certain education level
    user_salary_expectations = "user_salary_expectations"  # Increase relevancy when a user has a certain salary expectation
    user_desired_job_title = "user_desired_job_title"  # Increase relevancy when a user has a certain desired job title
    user_experience_level = "user_experience_level"  # Increase relevancy when a user has a certain experience level

    email = "email"  # Increases liklihood the job is featured in a users new job email

    pin_title_search = (
        "job_title_search"  # Increase relevancy when a user searches for a job title
    )
    pin_category = (
        "job_category"  # Increase relevancy when a user filters by job category
    )
    pin_experience_level = "job_experience_level"  # Increase relevancy when a user filters by experience level
    pin_education_level = "job_education_level"  # Increase relevancy when a user filters by education level
    pin_salary = "job_salary"  # Increase relevancy when a user filters by salary

    recommended_similiar_keywork = "recommended_similiar_keywork"  # Increase relevancy when a user searches for a job title
    recommended_similiar_category = "recommended_similiar_category"  # Increase relevancy when a user filters by job category
    recommended_similiar_experience_level = "recommended_similiar_experience_level"  # Increase relevancy when a user filters by experience level
    recommended_similiar_education_level = "recommended_similiar_education_level"  # Increase relevancy when a user filters by education level
    recommended_similiar_salary = "recommended_similiar_salary"  # Increase relevancy when a user filters by salary


# First page top
# Second page top etc.

# Recommended/relevant ads
