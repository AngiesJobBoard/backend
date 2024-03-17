from fastapi import APIRouter, status, File, Form, UploadFile, Request
from email import message_from_string

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
async def jobs_webhook_handler(request: Request, email: str = Form(...)):
    print(request.__dict__)
    email_message = message_from_string(email)
    subject = email_message.get('Subject')
    sender = email_message.get('From')
    recipients = email_message.get('To')
    if email_message.is_multipart():
        for part in email_message.walk():
            content_type = part.get_content_type()
            content_disposition = part.get("Content-Disposition")
            if content_type == "text/plain" and content_disposition is None:
                body = part.get_payload(decode=True).decode()
    else:
        body = email_message.get_payload(decode=True).decode()

    print(f"Email from: {sender}")
    print(f"Recipients: {recipients}")
    print(f"Subject: {subject}")
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
