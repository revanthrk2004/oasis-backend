import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, FileContent, FileName, FileType, Disposition
import base64
import os

def send_email(to, subject, content, attachment=None, filename=None):
    try:
        sg = sendgrid.SendGridAPIClient(api_key=os.getenv("SENDGRID_API_KEY"))
        email = Mail(
            from_email=Email("oasisappreset@gmail.com"),
            to_emails=To(to),
            subject=subject,
            plain_text_content=Content("text/plain", content)
        )

        # If attachment is provided
        if attachment and filename:
            encoded_file = base64.b64encode(attachment.read()).decode()
            attached_file = Attachment(
                FileContent(encoded_file),
                FileName(filename),
                FileType("image/png"),
                Disposition("attachment")
            )
            email.attachment = attached_file

        response = sg.send(email)
        return response.status_code < 400
    except Exception as e:
        print(f"SendGrid Error: {e}")
        return False
