#!/usr/bin/env python
"""
FALL DETECTION SYSTEM - LIVE WEBCAM DEMO
Real-time detection with pose skeleton overlay and metrics
"""

import cv2
import numpy as np
from ultralytics import YOLO
from fall_logic import FallLogic
import threading
import time

class LiveDemoCamera:
    def __init__(self):
        """Initialize YOLOv8 model and fall detection logic."""
        print("🔧 Loading YOLOv8 Pose Model...")
        try:
            self.model = YOLO("yolov8n-pose.pt")
            print("✅ Model loaded successfully!\n")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            print("Make sure yolov8n-pose.pt is in the current directory")
            raise
        
        self.fall_logic = FallLogic()
        self.cap = None
        self.running = False
        self.person_id = 1
        
        # Display settings
        self.frame_count = 0
        self.fps_start_time = time.time()
        self.fps = 0
        
    def setup_camera(self):
        """Initialize webcam capture."""
        print("📷 Initializing Webcam...")
        self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            print("❌ Error: Could not open webcam")
            return False
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        print("✅ Webcam ready!\n")
        return True
    
    def draw_skeleton(self, frame, keypoints):
        """Draw pose skeleton on frame."""
        if keypoints is None:
            return frame
        
        # COCO keypoints connections: 17 points
        connections = [
            # Head
            (0, 1), (0, 2), (1, 3), (2, 4),
            # Body
            (5, 6), (5, 7), (6, 8), (7, 9), (8, 10),
            (5, 11), (6, 12), (11, 12),
            # Legs
            (11, 13), (12, 14), (13, 15), (14, 16)
        ]
        
        # Draw keypoints
        for kpt in keypoints:
            x, y, conf = int(kpt[0]), int(kpt[1]), kpt[2]
            if conf > 0.5:  # Only draw if confident
                cv2.circle(frame, (x, y), 4, (0, 255, 0), -1)
        
        # Draw connections
        for start, end in connections:
            if (keypoints[start][2] > 0.5 and keypoints[end][2] > 0.5):
                x1, y1 = int(keypoints[start][0]), int(keypoints[start][1])
                x2, y2 = int(keypoints[end][0]), int(keypoints[end][1])
                cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        return frame
    
    def draw_info(self, frame, state, fall, debug, color):
        """Draw detection info and metrics on frame."""
        h, w = frame.shape[:2]
        
        # State box background
        cv2.rectangle(frame, (10, 10), (350, 150), (0, 0, 0), -1)
        cv2.rectangle(frame, (10, 10), (350, 150), color, 2)
        
        # State text (large)
        font = cv2.FONT_HERSHEY_SIMPLEX
        state_text = f"STATE: {state}"
        cv2.putText(frame, state_text, (20, 50), font, 1.2, color, 3)
        
        # Fall alert
        fall_text = "🚨 FALL DETECTED!" if fall else "Status: OK"
        fall_color = (0, 0, 255) if fall else (0, 255, 0)
        cv2.putText(frame, fall_text, (20, 85), font, 1, fall_color, 3)
        
        # Metrics
        metrics_y = 120
        metrics_text = f"Accel: {debug.get('peak_acceleration', 0):.0f} | Smooth: {debug.get('velocity_smoothness', 0):.0f}"
        cv2.putText(frame, metrics_text, (20, metrics_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        
        # FPS counter
        fps_text = f"FPS: {self.fps:.1f}"
        cv2.putText(frame, fps_text, (w - 150, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        
        # Instructions
        instructions = "Press 'Q' to quit | 'R' to reset"
        cv2.putText(frame, instructions, (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
        
        return frame
    
    def process_frame(self, frame):
        """Process single frame: detect pose, classify state."""
        # Run detection
        results = self.model(frame, verbose=False)
        
        if not results or len(results) == 0:
            return frame, "No Pose", (100, 100, 100), False, {}
        
        result = results[0]
        keypoints = result.keypoints.data
        
        if len(keypoints) == 0:
            return frame, "No Person", (100, 100, 100), False, {}
        
        # Get first person's keypoints
        person_kpts = keypoints[0].cpu().numpy()
        
        # Update fall logic
        state, color_tuple, fall, debug = self.fall_logic.update(self.person_id, person_kpts)
        
        # Use color from logic directly (already BGR)
        color_bgr = tuple(int(c) for c in color_tuple)
        
        # Draw skeleton
        frame = self.draw_skeleton(frame, person_kpts)
        
        return frame, state, color_bgr, fall, debug
    
    def calculate_fps(self):
        """Calculate frames per second."""
        self.frame_count += 1
        current_time = time.time()
        elapsed = current_time - self.fps_start_time
        
        if elapsed >= 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.fps_start_time = current_time
    
    def run(self):
        """Main demo loop."""
        if not self.setup_camera():
            return
        
        print("🎥 Starting Live Demo...")
        print("   Press 'Q' to quit")
        print("   Press 'R' to reset tracking\n")
        
        self.running = True
        alert_count = 0
        
        try:
            while self.running:
                ret, frame = self.cap.read()
                
                if not ret:
                    print("❌ Error reading frame")
                    break
                
                # Flip for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Process frame
                frame, state, color, fall, debug = self.process_frame(frame)
                
                # Draw info
                frame = self.draw_info(frame, state, fall, debug, color)
                
                # Calculate FPS
                self.calculate_fps()
                
                # Fall alert
                if fall and alert_count == 0:
                    alert_count += 1
                    print("\n🚨 FALL DETECTED!")
                    print(f"   State: {state}")
                    print(f"   Acceleration: {debug.get('peak_acceleration', 0):.1f}")
                    print(f"   Velocity: {debug.get('velocity', 0):.1f}\n")
                elif not fall:
                    alert_count = 0
                
                # Display frame
                cv2.imshow("Fall Detection System - Live Demo", frame)
                
                # Keyboard controls
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q') or key == ord('Q'):
                    print("\n👋 Exiting...")
                    self.running = False
                elif key == ord('r') or key == ord('R'):
                    print("🔄 Resetting tracking...")
                    self.fall_logic = FallLogic()
                    self.person_id += 1
        
        except KeyboardInterrupt:
            print("\n⚠️ Interrupted by user")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        self.running = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("✅ Demo ended")

def main():
    """Main entry point."""
    print("\n" + "="*70)
    print("  FALL DETECTION SYSTEM - LIVE WEBCAM DEMO")
    print("  Real-time pose detection with fall alerts")
    print("="*70 + "\n")
    
    try:
        demo = LiveDemoCamera()
        demo.run()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        print("Troubleshooting:")
        print("  1. Check webcam is connected and working")
        print("  2. Verify yolov8n-pose.pt is in current directory")
        print("  3. Check all dependencies are installed: pip install -r requirements.txt")

if __name__ == "__main__":
    main()
