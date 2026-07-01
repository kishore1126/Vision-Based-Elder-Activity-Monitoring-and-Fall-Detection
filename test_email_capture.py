import cv2
import numpy as np
import os
from flask import Flask
from email_service import send_alert_email
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_test():
    # 1. Create a mock Flask app context (needed for send_alert_email)
    app = Flask(__name__)
    
    # 2. Get registered email from user input or environment
    target_email = os.environ.get('EMAIL_USER')
    if not target_email:
        target_email = input("Enter the destination email for this test: ")
    
    print(f"Starting email capture test to: {target_email}")
    
    # 3. Create a sample image (640x480 black image with text)
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(image, "TEST FALL CAPTURE", (100, 240), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
    cv2.putText(image, f"Time: {time.ctime()}", (100, 300), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    # Draw a mock bounding box
    cv2.rectangle(image, (150, 100), (500, 400), (0, 0, 255), 2)
    cv2.putText(image, "STATE: Sudden Fall", (150, 90), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # 4. Encode image to JPEG bytes
    success, buffer = cv2.imencode('.jpg', image)
    if not success:
        print("Failed to encode test image")
        return
    image_bytes = buffer.tobytes()

    # 5. Call the email service
    print("Calling email service...")
    send_alert_email(app, target_email, image_bytes)
    
    print("\n[SUCCESS] Test initiated!")
    print("The email is being sent in a background thread.")
    print("Waiting 5 seconds for background thread to complete...")
    time.sleep(5)
    print(f"Test complete. Please check {target_email}.")

if __name__ == "__main__":
    run_test()
