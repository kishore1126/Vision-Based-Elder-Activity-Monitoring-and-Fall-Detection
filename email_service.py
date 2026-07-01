import smtplib
from email.message import EmailMessage
import os
import threading

# attempt to load environment from .env file if present (makes development easier)
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

# helper to fetch env var with debug

def _env(name):
    val = os.environ.get(name)
    if val is None:
        print(f"Warning: environment variable {name} not set")
    return val

def send_async_email(app, msg):
    with app.app_context():
        try:
            # Use variables from .env or defaults
            smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.environ.get('SMTP_PORT', 587))
            
            print(f"Attempting to send email to: {msg['To']} via {smtp_server}:{smtp_port}")
            
            with smtplib.SMTP(smtp_server, smtp_port) as smtp:
                smtp.set_debuglevel(1) # Enable debug output for terminal
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
                
                user = _env('EMAIL_USER')
                pw = _env('EMAIL_PASS')
                
                if not user or not pw:
                    print("Error: EMAIL_USER or EMAIL_PASS environment variables not set."
                          " make sure they are exported in the shell or placed in a .env file.")
                    return
                    
                smtp.login(user, pw)
                smtp.send_message(msg)
                print("Email alert sent successfully!")
        except Exception as e:
            print(f"CRITICAL: Failed to send email alert: {e}")
            import traceback
            traceback.print_exc()

def send_alert_email(app, user_email, image_data=None):
    sender = os.environ.get('EMAIL_USER')
    if not sender:
        print("CRITICAL ERROR: EMAIL_USER not set in environment!")
        return
        
    msg = EmailMessage()
    msg['Subject'] = '🚨 URGENT: Fall Detected with Capture! 🚨'
    msg['From'] = sender
    msg['To'] = user_email
    
    body = f'EMERGENCY: A fall has been detected for monitoring session: {user_email}.\n\nA capture of the event is attached to this email.'
    msg.set_content(body)

    # Attach image if provided
    if image_data is not None:
        try:
            msg.add_attachment(
                image_data,
                maintype='image',
                subtype='jpeg',
                filename='fall_capture.jpg'
            )
            print("Image capture attached to email.")
        except Exception as e:
            print(f"Error attaching image: {e}")

    thread = threading.Thread(target=send_async_email, args=(app, msg))
    thread.daemon = True
    thread.start()
