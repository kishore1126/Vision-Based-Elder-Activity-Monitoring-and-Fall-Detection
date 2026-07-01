#!/usr/bin/env python
"""
TEST EMAIL SENDING
Send a sample email to verify the email service works
"""

import os
import smtplib
from email.message import EmailMessage

def test_email():
    """Send a test email to ksanjuma1234@gmail.com"""

    # Email configuration
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587

    # Get credentials from environment or prompt
    email_user = os.environ.get('EMAIL_USER')
    email_pass = os.environ.get('EMAIL_PASS')

    if not email_user:
        email_user = input("Enter your Gmail address: ")
    if not email_pass:
        email_pass = input("Enter your Gmail app password: ")

    # Create email message
    msg = EmailMessage()
    msg['Subject'] = 'FALL DETECTION SYSTEM - Test Email'
    msg['From'] = email_user
    msg['To'] = 'kishore5758s@gmail.com'

    msg.set_content("""
    This is a test email from your Fall Detection System.

    If you received this email, the email service is working correctly!

    The system can now send alerts when falls are detected.

    Best regards,
    Fall Detection System
    """)

    try:
        print(f"📧 Sending test email to: {msg['To']}")
        print(f"📨 From: {msg['From']}")
        print(f"🔗 Server: {smtp_server}:{smtp_port}")

        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            smtp.set_debuglevel(1)
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()

            print("🔐 Logging in...")
            smtp.login(email_user, email_pass)

            print("📤 Sending message...")
            smtp.send_message(msg)

        print("✅ SUCCESS: Test email sent successfully!")
        print("📬 Check kishore5758s@gmail.com for the test message")

    except Exception as e:
        print(f"❌ ERROR: Failed to send email: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure EMAIL_USER and EMAIL_PASS are set in environment variables")
        print("2. For Gmail, use an App Password instead of your regular password")
        print("3. Enable 'Less secure app access' or use App Passwords")
        print("4. Check your internet connection")
        print("5. Verify the recipient email address")

if __name__ == "__main__":
    test_email()
