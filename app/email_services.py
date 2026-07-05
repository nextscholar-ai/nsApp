import smtplib
import os

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


# =========================
# CORE EMAIL SENDER
# =========================

def send_email(to_email: str, subject: str, body: str):

    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.set_debuglevel(0)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)

        server.send_message(msg)
        server.quit()

        print(f"Email sent OK -> to={to_email} subject={subject}")
        return True

    except Exception as e:

        print("Email error:", e)
        return False


# =========================
# OTP EMAIL
# =========================

def send_otp_email(email: str, otp: str, purpose: str = "verification"):

    if purpose == "login":
        subject = "Login OTP - Student ERP"
        reason_line = "Your OTP for login is"
    else:
        subject = "Email Verification OTP - Student ERP"
        reason_line = "Your OTP for email verification is"

    body = f"""
{reason_line}: {otp}

This OTP is valid for 10 minutes.
Do not share it with anyone.
"""

    return send_email(email, subject, body)


# =========================
# RESET PASSWORD EMAIL
# =========================

def send_reset_email(email: str, link: str):

    subject = "Password Reset Request"

    body = f"""
Click below to reset password:

{link}

This link expires in 30 minutes.
"""

    return send_email(email, subject, body)


# =========================
# VERIFICATION EMAIL
# =========================

def send_verification_email(email: str, link: str):
    subject = "Verify Your Email"

    body = f"""
Please verify your email by clicking the link below:

{link}
"""

    return send_email(email, subject, body)