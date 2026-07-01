import cv2
import numpy as np
from datetime import datetime
from email_service import send_alert_email
import threading
import time
import pyttsx3
from collections import deque
from ultralytics import YOLO
import torch
from fall_logic import FallLogic

class VideoCamera(object):
    def __init__(self, app, user_email):
        self.app = app
        self.user_email = user_email
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # 1. Optimize GPU
        self.optimize_gpu()
        
        # 2. Load Model
        self.load_model()
        
        # 3. Initialize Camera
        self.capture_frames()
        
        # System State
        self.current_status = "Initializing..."
        self.current_details = {"angle": 0, "state": "None", "is_fall": False, "fps": 0}
        self.device_name = torch.cuda.get_device_name(0) if self.device == 'cuda' else "CPU"
        self.email_sent = False
        self.frame_bytes = None
        self.keep_running = True
        self.lock = threading.Lock()
        
        # Logic & Metrics
        self.logic = FallLogic()
        self.fps_deque = deque(maxlen=30)
        self.last_time = time.time()
        
        # Start Pipeline
        self.thread = threading.Thread(target=self.run_pipeline, args=())
        self.thread.daemon = True
        self.thread.start()

    def optimize_gpu(self):
        """Configure GPU settings for production performance."""
        if self.device == 'cuda':
            torch.backends.cudnn.benchmark = True
            torch.cuda.set_device(0)

    def load_model(self):
        """Load YOLOv8-Pose and optimize for inference."""
        try:
            print(f"Loading YOLOv8-Pose on {self.device}...")
            self.model = YOLO("yolov8n-pose.pt")
            self.model.to(self.device)
            if self.device == 'cuda':
                self.model.model.half() # FP16 Precision
            print("Model loaded and optimized.")
        except Exception as e:
            print(f"Model load failed: {e}")
            self.model = None

    def capture_frames(self):
        """Initialize camera with low buffer for real-time performance."""
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        
        # Force low latency
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

    def process_frame(self, frame):
        """Modular frame processing with mixed precision inference."""
        if self.model is None: return frame, "Model Error"

        # Resize for consistent performance
        frame = cv2.resize(frame, (640, 480))
        
        # Inference with Autocast (Mixed Precision)
        with torch.cuda.amp.autocast(enabled=(self.device == 'cuda')):
            results = self.model(frame, verbose=False, conf=0.5, device=self.device)[0]
        
        if len(results.boxes) == 0:
            self.current_status = "No person detected"
            return frame, self.current_status

        for i, box in enumerate(results.boxes):
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            keypoints = results.keypoints[i].data[0].cpu().numpy()
            
            # 1. Logic Update
            state, color, is_fall, debug_info = self.logic.update(i, keypoints)
            
            # 2. Performance Metrics
            self.update_metrics(debug_info, state, is_fall)
            
            # 3. Visualization (Draw BEFORE alert so capture includes labels)
            self.draw_skeleton(frame, keypoints, (int(x1), int(y1), int(x2), int(y2)), state, color, is_fall)
            
            # 4. Handle Alerts with Capture
            if is_fall and not self.email_sent:
                self.trigger_emergency(state, frame.copy())
            elif not is_fall and state in ["Standing", "Sitting"]:
                self.email_sent = False

        return frame, "Active"

    def draw_skeleton(self, frame, keypoints, bbox, state, color, is_fall):
        """Draw full skeleton and labels on the frame."""
        x1, y1, x2, y2 = bbox
        
        # BBox & Label
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = f"STATE: {state}"
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # Full Skeleton Connections
        connections = [
            (0, 1), (0, 2), (1, 3), (2, 4), # Head
            (5, 6), (5, 7), (7, 9), (6, 8), (8, 10), # Arms
            (5, 11), (6, 12), (11, 12), # Torso
            (11, 13), (13, 15), (12, 14), (14, 16) # Legs
        ]
        
        for pair in connections:
            p1, p2 = keypoints[pair[0]], keypoints[pair[1]]
            if p1[2] > 0.4 and p2[2] > 0.4:
                cv2.line(frame, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), color, 2)

        for kp in keypoints:
            if kp[2] > 0.4:
                cv2.circle(frame, (int(kp[0]), int(kp[1])), 4, color, -1)

        if is_fall:
            cv2.putText(frame, "EMERGENCY: FALL!", (50, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 4)

    def trigger_emergency(self, state, frame=None):
        """Initiate emergency protocols with optional image capture."""
        print(f"!!! EMERGENCY: {state} !!! Sending alert with capture to: {self.user_email}")
        self.current_status = "FALL DETECTED!"
        
        # Prepare image capture for email
        image_data = None
        if frame is not None:
            success, buffer = cv2.imencode('.jpg', frame)
            if success:
                image_data = buffer.tobytes()
        
        send_alert_email(self.app, self.user_email, image_data)
        self.play_fall_alert()
        self.email_sent = True
        
        # Log to DB
        try:
            from models import db, FallLog
            with self.app.app_context():
                db.session.add(FallLog(status="Fall Detected", timestamp=datetime.now()))
                db.session.commit()
        except Exception as e: print(f"DB Log error: {e}")

    def update_metrics(self, debug_info, state, is_fall):
        """Calculate and update system performance metrics."""
        curr_time = time.time()
        self.fps_deque.append(1.0 / (curr_time - self.last_time + 1e-6))
        self.last_time = curr_time
        avg_fps = sum(self.fps_deque) / len(self.fps_deque)
        
        self.current_details = {
            "angle": debug_info.get("angle", 0),
            "state": state,
            "is_fall": is_fall,
            "fps": round(avg_fps, 1)
        }

    def run_pipeline(self):
        """Continuous non-blocking processing pipeline."""
        while self.keep_running:
            success, frame = self.cap.read()
            if not success:
                time.sleep(0.01)
                continue
                
            frame, status = self.process_frame(frame)
            
            # Thread-safe frame storage
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            with self.lock:
                self.frame_bytes = buffer.tobytes()
            
            time.sleep(0.001) # Yield to OS

    def play_fall_alert(self):
        """Sound alert thread."""
        def speak():
            try:
                import pythoncom
                pythoncom.CoInitialize()
                engine = pyttsx3.init()
                engine.say("Emergency! Fall detected. Please check the dashboard.")
                engine.runAndWait()
                engine.stop()
            except Exception as e: print(f"Audio error: {e}")
        threading.Thread(target=speak, daemon=True).start()

    def get_frame_bytes(self):
        with self.lock: return self.frame_bytes

    def __del__(self):
        self.keep_running = False
        if hasattr(self, 'cap'): self.cap.release()
