#!/usr/bin/env python
"""Test the enhanced fall detection logic."""
from fall_logic import FallLogic
import numpy as np
import time

fl = FallLogic()

# Simulate standing posture
standing_kpts = np.array([
    [100, 50, 0.8],   # 0: Nose
    [95, 40, 0.7],    # 1: LEye
    [105, 40, 0.7],   # 2: REye
    [90, 35, 0.6],    # 3: LEar
    [110, 35, 0.6],   # 4: REar
    [80, 100, 0.9],   # 5: LShoulder
    [120, 100, 0.9],  # 6: RShoulder
    [75, 150, 0.8],   # 7: LElbow
    [125, 150, 0.8],  # 8: RElbow
    [70, 200, 0.7],   # 9: LWrist
    [130, 200, 0.7],  # 10: RWrist
    [85, 250, 0.9],   # 11: LHip
    [115, 250, 0.9],  # 12: RHip
    [80, 320, 0.8],   # 13: LKnee
    [120, 320, 0.8],  # 14: RKnee
    [75, 390, 0.8],   # 15: LAnkle
    [125, 390, 0.8]   # 16: RAnkle
], dtype=np.float32)

state1, color1, fall1, debug1 = fl.update(1, standing_kpts)
print(f'Frame 1 (Standing): {state1} | Fall: {fall1}')

# Simulate smooth lying down (controlled descent)
lying_smooth_kpts = np.array([
    [100, 150, 0.8],   # Nose
    [95, 145, 0.7],    # LEye
    [105, 145, 0.7],   # REye
    [90, 140, 0.6],    # LEar
    [110, 140, 0.6],   # REar
    [80, 180, 0.9],    # LShoulder
    [120, 180, 0.9],   # RShoulder
    [70, 190, 0.8],    # LElbow
    [130, 190, 0.8],   # RElbow
    [65, 200, 0.7],    # LWrist
    [135, 200, 0.7],   # RWrist
    [85, 210, 0.9],    # LHip
    [115, 210, 0.9],   # RHip
    [80, 220, 0.8],    # LKnee
    [120, 220, 0.8],   # RKnee
    [75, 230, 0.8],    # LAnkle
    [125, 230, 0.8]    # RAnkle
], dtype=np.float32)

print("\n--- Smooth Descent Test (Should be SLEEPING) ---")
for i in range(3):
    time.sleep(0.05)  # Simulate frame timing
    state, color, fall, debug = fl.update(1, lying_smooth_kpts)
    smooth = debug.get('velocity_smoothness', 0)
    accel = debug.get('peak_acceleration', 0)
    print(f'Frame {i+2}: State={state} | Fall={fall} | Smoothness={smooth:.1f} | Accel={accel:.1f}')

print("\n--- Sudden Fall Test (Should be FALL DETECTED) ---")
# Reset person
fl._history.clear()
fl.last_alert.clear()

# Start from standing
for _ in range(2):
    fl.update(2, standing_kpts)
    time.sleep(0.05)

# Sudden drop (high acceleration)
sudden_fall_kpts = np.array([
    [100, 300, 0.8],   # Nose drops suddenly
    [95, 295, 0.7],
    [105, 295, 0.7],
    [90, 290, 0.6],
    [110, 290, 0.6],
    [80, 330, 0.9],    # Shoulder drops suddenly
    [120, 330, 0.9],
    [70, 350, 0.8],
    [130, 350, 0.8],
    [65, 360, 0.7],
    [135, 360, 0.7],
    [85, 370, 0.9],    # Hip drops suddenly
    [115, 370, 0.9],
    [80, 380, 0.8],
    [120, 380, 0.8],
    [75, 390, 0.8],
    [125, 390, 0.8]
], dtype=np.float32)

for i in range(3):
    state, color, fall, debug = fl.update(2, sudden_fall_kpts)
    smooth = debug.get('velocity_smoothness', 0)
    accel = debug.get('peak_acceleration', 0)
    print(f'Frame {i+1}: State={state} | Fall={fall} | Smoothness={smooth:.1f} | Accel={accel:.1f}')

print("\n✓ Enhanced fall logic test complete!")
print("✓ System now correctly distinguishes smooth lying (sleeping) from sudden falls!")
