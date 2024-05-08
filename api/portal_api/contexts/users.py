import json
from fastapi import APIRouter, Request, UploadFile, File, Body
from fastapi.responses import JSONResponse
from cachetools import TTLCache

from ajb.contexts.users.repository import UserRepository
from ajb.contexts.users.usecase import UserUseCase
from ajb.contexts.users.models import UpdateUser, User, UserProfileUpload
from ajb.contexts.companies.recruiters.repository import RecruiterRepository
from ajb.contexts.companies.recruiters.models import UserUpdateRecruiter, Recruiter
from ajb.contexts.companies.models import Company

from api.exceptions import NotFound, GenericHTTPException
from api.vendors import storage
from api.middleware import scope


router = APIRouter(tags=["Users"], prefix="/me")
verify_password_attempt_cache: TTLCache[str, int] = TTLCache(maxsize=1000, ttl=60)


@router.get("/", response_model=User)
def get_current_user(request: Request):
    return UserRepository(scope(request)).get(scope(request).user_id)


@router.patch("/", response_model=User)
def update_current_user(request: Request, user: UpdateUser):
    return UserRepository(scope(request)).update(scope(request).user_id, user)


@router.get("/companies/{company_id}/recruiter")
def get_me_as_a_recruiter(request: Request, company_id: str):
    return RecruiterRepository(scope(request), company_id).get_one(
        user_id=scope(request).user_id, company_id=company_id
    )


@router.patch("/companies/{company_id}/recruiter", response_model=Recruiter)
def update_me_as_a_recruiter(
    request: Request, company_id: str, updates: UserUpdateRecruiter
):
    recruiter_repo = RecruiterRepository(scope(request), company_id)
    recruiter = recruiter_repo.get_one(
        user_id=scope(request).user_id, company_id=company_id
    )
    if not recruiter:
        raise NotFound("Recruiter not found")

    return RecruiterRepository(scope(request), company_id).update(recruiter.id, updates)


@router.post("/profile-picture", response_model=User)
def update_current_user_profile_picture(request: Request, file: UploadFile = File(...)):
    data = UserProfileUpload(
        file_type=file.content_type if file.content_type else "image/png",
        file_name=file.filename if file.filename else "profile_picture",
        profile_picture_data=file.file.read(),
        user_id=scope(request).user_id,
    )
    return UserUseCase(scope(request), storage).update_profile_picture(data)


def check_password_attempt_cache(user_id: str):
    """
    Checks the cache for the number of attempts for a user ID.
    Raises an HTTPException if the number of attempts is 3 or more.
    """
    if user_id in verify_password_attempt_cache:
        attempts = verify_password_attempt_cache[user_id]
        if attempts >= 20:
            raise GenericHTTPException(status_code=429, detail="Too many attempts")
        else:
            verify_password_attempt_cache[user_id] += 1
    else:
        verify_password_attempt_cache[user_id] = 1


@router.post("/change-password", response_model=bool)
def change_password(
    request: Request, old_password: str = Body(...), new_password: str = Body(...)
):
    user_id = scope(request).user_id
    correct_password = UserUseCase(scope(request)).verify_password(
        user_id, old_password
    )
    if not correct_password:
        check_password_attempt_cache(user_id)
        raise GenericHTTPException(status_code=401, detail="Incorrect password")
    return UserUseCase(scope(request)).change_password(
        scope(request).user_id, new_password
    )


@router.post("/change-email", response_model=bool)
def change_email(request: Request, new_email: str = Body(...)):
    return UserUseCase(scope(request)).change_email(scope(request).user_id, new_email)


@router.post("/create-demo-company", response_model=Company)
def add_demo_company_to_user(request: Request):
    return UserUseCase(scope(request)).create_demo_company_for_user(
        scope(request).user_id
    )
