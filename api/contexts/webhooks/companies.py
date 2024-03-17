from fastapi import APIRouter, status, File, Form, UploadFile, Request
from email import message_from_bytes

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
async def jobs_webhook_handler(request: Request):
    # Assuming the raw email is sent in the request body, we read it as bytes.
    raw_email = await request.body()
    
    # Parse the raw email content.
    email_message = message_from_bytes(raw_email)
    
    # Extracting information from the parsed email.
    subject = email_message.get('Subject')
    sender = email_message.get('From')
    recipients = email_message.get('To')
    # Depending on the email content type, you might need to handle it differently.
    # This is a simple example to get the body for a plain text email.
    if email_message.is_multipart():
        for part in email_message.walk():
            content_type = part.get_content_type()
            content_disposition = part.get("Content-Disposition")
            if content_type == "text/plain" and content_disposition is None:
                body = part.get_payload(decode=True).decode()
    else:
        body = email_message.get_payload(decode=True).decode()
    
    # Process the email content as needed.
    # For this example, we'll just return some of the extracted information.
    return {
        "subject": subject,
        "sender": sender,
        "recipients": recipients,
        "body": body,
    }


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
