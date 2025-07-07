import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import requests
from dotenv import load_dotenv  # pip install python-dotenv

load_dotenv()  # reads .env into os.environ

# === CONFIG ===
SHEET_ID   = os.getenv("SHEET_ID")                      # 1F4vOx9UcTg...
SENDER     = os.getenv("GMAIL_SENDER")                  # your Gmail addr
RECEIVER   = os.getenv("RECEIVER_EMAIL")                # destination addr
APP_PASS   = os.getenv("GMAIL_APP_PASSWORD")            # 16‑char app pw
SUBJECT    = "Weekly Property  Listings Digest (CSV Attached)"

def download_sheet(sheet_id: str) -> bytes:
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    r = requests.get(url, timeout=30)
    r.raise_for_status()                     # raises on 4xx/5xx
    if not r.content.strip():
        raise ValueError("Downloaded sheet is empty.")
    return r.content

def build_email(csv_blob: bytes) -> MIMEMultipart:
    msg = MIMEMultipart()
    msg["From"], msg["To"], msg["Subject"] = SENDER, RECEIVER, SUBJECT
    attachment = MIMEApplication(csv_blob, Name="Property_listings.csv")
    attachment["Content-Disposition"] = 'attachment; filename="Property_listings.csv"'
    msg.attach(attachment)
    return msg

def send_email(msg: MIMEMultipart) -> None:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(SENDER, APP_PASS)
        smtp.send_message(msg)

def send_digest():
    try:
        csv_bytes = download_sheet(SHEET_ID)
        email_msg = build_email(csv_bytes)
        send_email(email_msg)
        print("✅ Weekly digest sent.")
    except Exception as e:
        # In production you might log to a file, Sentry, etc.
        print(f"❌ Digest failed: {e}")

if __name__ == "__main__":
    send_digest()
