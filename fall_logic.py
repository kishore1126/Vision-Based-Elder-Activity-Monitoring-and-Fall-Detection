import time
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


class FallLogic:
    GREEN = (0, 255, 0)      
    ORANGE = (0, 165, 255)   
    CYAN = (255, 255, 0)     
    RED = (0, 0, 255)       
    GRAY = (128, 128, 128)  

    def __init__(self, history_len: int = 15, debug: bool = False):
        self.history_len = history_len
        self.debug = debug
        self._history: Dict[Any, deque] = {}
        self.alerted: Dict[Any, bool] = {}
        self.last_alert: Dict[Any, float] = {}

    def update(self, person_key: Any, kps: np.ndarray):
        """Update person's posture state. Returns: (state, color, is_fall, debug_info)"""
        now = time.time()
        
       
        if person_key not in self._history:
            self._history[person_key] = deque(maxlen=self.history_len)
            self.alerted[person_key] = False
            self.last_alert[person_key] = 0.0

        history = self._history[person_key]
       
        features = self._extract_features(kps)
        
        prev_frame = list(history)[-1] if history else None
        velocity_y = self._calculate_velocity(prev_frame, features, now)
        
        torso_angle = features.get("torso_angle", 0)
        posture = self._classify_posture(torso_angle, features)
        
        
        frame_data = {
            "time": now,
            "center_y": features.get("center_y"),
            "angle": torso_angle,
            "posture": posture,
            "velocity_y": velocity_y,
        }
        history.append(frame_data)
        
        
        is_sleeping = posture == "Lying" and self._lying_duration(history) >= 10.0 and self._is_stable(history)
        
        
        is_fall = False
        if posture == "Lying" and not is_sleeping:
            is_fall = self._detect_fall(person_key, history, now)
        
      
        if is_fall:
            state = "Fall Detected"
            color = self.RED
            self.alerted[person_key] = True
            self.last_alert[person_key] = now
        elif is_sleeping:
            state = "Sleeping"
            color = self.CYAN
        elif posture == "Standing":
            state = "Standing"
            color = self.GREEN
        elif posture == "Sitting":
            state = "Sitting"
            color = self.ORANGE
        elif posture == "Lying":
            state = "Lying"
            color = self.CYAN
        else:
            state = "Unknown"
            color = self.GRAY
        
        debug_info = {
            "angle": torso_angle,
            "velocity_y": velocity_y,
            "posture": posture,
            "is_fall": is_fall,
        }
        
        return state, color, is_fall, debug_info
    
    def _extract_features(self, kps: np.ndarray) -> Dict[str, Optional[float]]:
        """Extract features from keypoints."""
        if kps is None or len(kps) < 17:
            return {"valid": False}
        
        try:
            points = np.asarray(kps, dtype=np.float32)
            visible = points[:, 2] > 0.3
            if not np.any(visible):
                return {"valid": False}
            
            
            shoulder_l, shoulder_r = points[5, :2], points[6, :2]
            hip_l, hip_r = points[11, :2], points[12, :2]
            knee_l, knee_r = points[13, :2], points[14, :2]
            ankle_l, ankle_r = points[15, :2], points[16, :2]
            
            
            shoulder = (shoulder_l + shoulder_r) / 2.0
            hip = (hip_l + hip_r) / 2.0
            
            
            torso_vec = hip - shoulder
            torso_angle = float(np.degrees(np.arctan2(abs(torso_vec[1]), abs(torso_vec[0]))))
            
           
            knee = (knee_l + knee_r) / 2.0
            ankle = (ankle_l + ankle_r) / 2.0
            hip_to_knee = float(np.linalg.norm(knee - hip))
            hip_to_ankle = float(np.linalg.norm(ankle - hip))
            hip_to_knee_vert = float(abs(knee[1] - hip[1]))
            knee_to_ankle_vert = float(abs(ankle[1] - knee[1]))

            
            coords = points[visible, :2]
            width = float(np.max(coords[:, 0]) - np.min(coords[:, 0]))
            height = float(np.max(coords[:, 1]) - np.min(coords[:, 1]))
            center_y = float(np.mean(coords[:, 1]))
            aspect_ratio = height / max(width, 1.0)
            
            return {
                "valid": True,
                "center_y": center_y,
                "torso_angle": torso_angle,
                "hip_to_knee": hip_to_knee,
                "hip_to_ankle": hip_to_ankle,
                "hip_to_knee_vert": hip_to_knee_vert,
                "knee_to_ankle_vert": knee_to_ankle_vert,
                "aspect_ratio": aspect_ratio,
            }
        except Exception:
            return {"valid": False}
    
    def _classify_posture(self, angle: float, features: Dict) -> str:
        """Classify posture using torso angle plus leg configuration and compactness."""
        if not features.get("valid"):
            return "Unknown"

        hip_to_knee = features.get("hip_to_knee", 999)
        hip_to_ankle = features.get("hip_to_ankle", 999)
        hip_to_knee_vert = features.get("hip_to_knee_vert", 999)
        knee_to_ankle_vert = features.get("knee_to_ankle_vert", 999)
        aspect_ratio = features.get("aspect_ratio", 1.0)

       
        strong_sitting = (
            hip_to_knee_vert < 110.0
            and hip_to_ankle < 160.0
        )
        loose_sitting = (
            hip_to_knee_vert < 125.0
            and hip_to_ankle < 180.0
            and aspect_ratio < 1.6
        )
        compact_sitting = aspect_ratio < 1.7 and hip_to_knee_vert < 140.0

        if angle >= 70.0:
            if strong_sitting:
                return "Sitting"
            return "Standing"
        elif 25.0 <= angle < 70.0:
            if strong_sitting or loose_sitting or compact_sitting:
                return "Sitting"
            return "Standing"
        elif 20.0 <= angle < 25.0:
            if strong_sitting or loose_sitting:
                return "Sitting"
            return "Lying"
        else:
            return "Lying"
    
    def _calculate_velocity(self, prev: Optional[Dict], features: Dict, now: float) -> float:
        """Calculate vertical velocity."""
        if prev is None or prev.get("center_y") is None or features.get("center_y") is None:
            return 0.0
        dt = max(now - float(prev["time"]), 0.001)
        dy = float(features["center_y"]) - float(prev["center_y"])
        return dy / dt
    
    def _lying_duration(self, history: deque) -> float:
        """Return how long the person has been continuously lying."""
        if not history or history[-1].get("posture") != "Lying":
            return 0.0

        duration = 0.0
        recent = list(history)[::-1]
        last_time = recent[0].get("time", 0.0)

        for frame in recent:
            if frame.get("posture") != "Lying":
                break
            duration = last_time - float(frame.get("time", last_time))

        return duration

    def _is_stable(self, history: deque) -> bool:
        """Check if motion is very stable (for sleeping detection)."""
        if len(history) < 5:
            return False

       
        recent_velocities = [float(f.get("velocity_y", 0)) for f in list(history)[-5:]]
        downward_velocities = [v for v in recent_velocities if v > 0]
        max_velocity = max(downward_velocities, default=0)

        
        return max_velocity < 15.0

    def _detect_fall(self, person_key: Any, history: deque, now: float) -> bool:
        """Detect fall: ONLY sudden change from Standing to Lying."""
        if len(history) < 3:
            return False
        
        recent = list(history)[-5:]
        current_posture = recent[-1].get("posture")
        
        
        if current_posture != "Lying":
            return False
        
        
        was_standing_recently = False
        transition_time = None
        
        
        for i in range(len(recent) - 2, -1, -1):  
            prev_posture = recent[i].get("posture")
            if prev_posture == "Standing":
                was_standing_recently = True
                transition_time = now - recent[i].get("time", now)
                break
        
        # No recent Standing posture = not a fall
        if not was_standing_recently or transition_time is None:
            return False
        
        # Transition must be very sudden (within 1.0 second)
        if transition_time > 1.0:
            return False
        
        # Check for sudden downward motion, not just any fast movement
        velocities = [float(f.get("velocity_y", 0)) for f in recent]
        downward_velocities = [v for v in velocities if v > 0]
        max_downward = max(downward_velocities, default=0)
        
        # Require a sharp downward velocity for fall detection
        sudden_movement = max_downward > 120.0
        
        # Cooldown check to prevent alert spam
        if person_key in self.last_alert:
            if (now - self.last_alert[person_key]) < 3.0:
                return False
        
        return sudden_movement
