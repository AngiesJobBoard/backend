from fastapi import APIRouter, status, File, Form, UploadFile, Request

from ajb.base import RequestScope
from api.vendors import db


WEBHOOK_REQUEST_SCOPE = RequestScope(
    user_id="companies_webhook", db=db, company_id=None
)


router = APIRouter(
    tags=["Webhooks"],
    prefix="/webhooks/companies",
)


@router.post("/jobs", status_code=status.HTTP_204_NO_CONTENT)
async def jobs_webhook_handler(
    subject: str = Form(...),
    from_: str = Form(..., alias="from"),
    to: str = Form(...),
    text: str | None = Form(None),
):
    # Process the received data here
    print(f"Subject: {subject}")
    print(f"From: {from_}")
    print(f"To: {to}")
    print(f"Text: {text}")
    return {"message": "Email received successfully"}


@router.post("/applicants", status_code=status.HTTP_204_NO_CONTENT)
async def applicants_webhook_handler(
    from_email: str = Form(...),
    subject: str = Form(...),
    files: list[UploadFile] = File(default=None),
):
    print(f"Email from: {from_email}")
    print(f"Subject: {subject}")

    for file in files:
        contents = await file.read()
        # with open(file_location, "wb") as f:
        # f.write(contents)
        print(f"Saved file: {file.filename}")

    return {"message": "Email received successfully"}
