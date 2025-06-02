import sendgrid
from sendgrid.helpers.mail import Mail
import os

def send_email(to, subject, content):
    try:
        sg = sendgrid.SendGridAPIClient(api_key=os.getenv("SENDGRID_API_KEY"))
        email = Mail(
            from_email="oasisappreset@gmail.com",
            to_emails=to,
            subject=subject,
            plain_text_content=content
        )
        response = sg.send(email)
        return response.status_code < 400
    except Exception as e:
        print(f"SendGrid Error: {e}")
        return False
