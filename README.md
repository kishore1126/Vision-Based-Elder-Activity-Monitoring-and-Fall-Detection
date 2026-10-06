# 🛡️ Elder Guard — Vision-Based Elder Activity Monitoring & Fall Detection

A real-time, camera-based system that watches over elderly people, classifies their activity (**Standing, Sitting, Sleeping, Fall**) using human pose estimation, and instantly sends **email + audio alerts** when a fall is detected. It ships with a Flask web dashboard for live monitoring and fall history.

> No wearable needed. A normal webcam and a rule-based motion analysis on top of YOLOv8-Pose do all the work.

---

## ✨ Features

- **Real-time pose estimation** with YOLOv8 Nano Pose (17 COCO keypoints), 30+ FPS on CPU, faster on GPU
- **Activity classification:** Standing, Sitting, Sleeping (smooth lying) and Fall (sudden lying)
- **Fall vs. sleep differentiation** using motion quality (velocity, acceleration, smoothness) and not posture alone
- **Instant alerts:** email notification to the logged-in user + text-to-speech audio alert (`pyttsx3`)
- **Web dashboard (Flask):** user registration/login, live annotated video feed, current status, and fall history log
- **Alert cooldown** to avoid repeated email spam
- **Demo & test scripts** to verify the logic without a webcam
- **Optional GPU setup** (CUDA 12.1) via `setup_gpu.bat`

---

## 🧠 How It Works

```
Webcam (30 FPS)
      │
      ▼
YOLOv8-Pose (yolov8n-pose.pt)  →  17-point skeleton
      │
      ▼
Fall Logic (fall_logic.py)
  ├─ Posture classification (torso angle, leg alignment, bbox aspect ratio)
  └─ Motion analysis (peak velocity, peak acceleration, smoothness)
      │
      ▼
Decision Engine  →  Standing / Sitting / Sleeping / Fall
      │
      ├─ Fall → Email alert + audio alert + log to database
      ▼
Flask Dashboard (live feed, status, history)
```

### Posture classification

| Posture  | Rule (geometry of keypoints)                                  |
|----------|---------------------------------------------------------------|
| Standing | Torso angle > 70°, legs roughly vertical                      |
| Sitting  | Torso angle 35–70°, knees/ankles close to hips                |
| Lying    | Torso angle < 30°, near-horizontal body / wide bounding box   |

### Fall vs. sleep (motion analysis)

| Event    | Condition                                                                                                           |
|----------|---------------------------------------------------------------------------------------------------------------------|
| **Fall** | Standing/Sitting → Lying within ~1.2 s, peak acceleration > 300 px/s², high velocity, jerky motion                  |
| **Sleep**| Smooth transition to Lying, peak acceleration < 200 px/s², low smoothness score, sustained for > 0.5 s              |

Thresholds are physics-based rules (no model training required) and can be tuned in `fall_logic.py`.

---

## 📁 Project Structure

```
├── app.py                  # Flask server: auth, dashboard, video feed, status & history APIs
├── camera.py               # YOLOv8 + threaded video pipeline (VideoCamera)
├── fall_logic.py           # Core posture + motion analysis and fall decision logic
├── models.py               # SQLAlchemy models (User, FallLog)
├── email_service.py        # Email alert sending
├── templates/              # login, register, dashboard, base HTML templates
├── DEMO_ALL_STATES.py      # Synthetic demo of all 4 states (no webcam needed)
├── run_live_demo.py        # Live webcam demo with skeleton overlay
├── DEMO_COMMANDS.txt       # Handy demo commands
├── EMAIL_SETUP_GUIDE.py    # Guide for configuring email alerts
├── PROJECT_REVIEW_GUIDE.md # Detailed review / presentation guide
├── test_*.py, verify_system.py   # Email, logic and system tests
├── run.bat / setup_gpu.bat # Windows launcher and GPU setup scripts
├── requirements.txt        # Python dependencies
└── .env.example            # Configuration template
```

---

## 🧰 Tech Stack

- **Language:** Python 3.8+
- **Computer vision:** OpenCV, Ultralytics YOLOv8-Pose
- **Deep learning:** PyTorch
- **Backend:** Flask, Flask-SQLAlchemy, Flask-Login (SQLite)
- **Alerts:** SMTP email (Gmail App Password), pyttsx3 text-to-speech
- **Config:** python-dotenv

---

## ⚙️ Installation

```bash
# 1. Clone the repository
git clone https://github.com/kishore1126/Vision-Based-Elder-Activity-Monitoring-and-Fall-Detection.git
cd Vision-Based-Elder-Activity-Monitoring-and-Fall-Detection

# 2. (Recommended) create a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

# 3. Install dependencies
pip install -r requirements.txt
```

**GPU (optional, NVIDIA CUDA 12.1):** run `setup_gpu.bat` or

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

> `pywin32` in `requirements.txt` is Windows-only. On Linux/macOS, remove that line before installing.
> The YOLOv8 pose weights (`yolov8n-pose.pt`) are downloaded automatically by Ultralytics on first run if not present.

---

## 🔐 Configuration

Copy `.env.example` to `.env` and fill in your values:

```env
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password        # Gmail: create an App Password in Google Account security settings
SECRET_KEY=change-this-to-a-random-string
DATABASE_URL=sqlite:///db.sqlite
DEBUG=0
ALERT_COOLDOWN=10                   # seconds between repeated alert emails
FPS_LIMIT=30
RESOLUTION=640x480
```

⚠️ Never commit your real `.env` file. Use a strong, unique `SECRET_KEY` outside of demos.

See `EMAIL_SETUP_GUIDE.py` for step-by-step email setup, and test it with `python test_email.py`.

---

## ▶️ Usage

### 1. Synthetic demo (no webcam needed)
```bash
python DEMO_ALL_STATES.py
```
Runs test cases for Standing, Sitting, Sleeping and Fall and prints PASS/FAIL with acceleration metrics.

### 2. Live webcam demo
```bash
python run_live_demo.py
```
Shows the pose skeleton overlay with live state and metrics.
Colors: 🟢 Standing · 🟠 Sitting · 🔵 Sleeping · 🔴 Fall.
Controls: `Q` to quit, `R` to reset person tracking.

### 3. Web dashboard
```bash
python app.py
```
Open **http://localhost:5000**, register an account, log in, and open the dashboard. Fall alerts are emailed to the address you registered with.

| Route         | Description                                  |
|---------------|----------------------------------------------|
| `/register`   | Create an account                            |
| `/login`      | Sign in                                      |
| `/dashboard`  | Live monitoring page                         |
| `/video_feed` | MJPEG stream of the annotated camera feed    |
| `/status`     | Current state, angle and fall flag (JSON)    |
| `/history`    | Last 10 fall/activity log entries (JSON)     |

---

## 🧪 Testing

```bash
python verify_system.py        # overall system check
python test_enhanced_logic.py  # fall/sleep logic tests
python test_email_mock.py      # email flow with a mock SMTP
python test_email.py           # real email test (needs .env)
```

Suggested manual scenarios: stand, sit, lie down slowly (→ Sleeping), walk then drop suddenly (→ Fall), leave the frame (→ no alert), partially visible body (→ graceful degradation).

---

## 💻 System Requirements

- **OS:** Windows 10/11, Linux or macOS
- **Python:** 3.8+
- **CPU/RAM:** Intel i5 / Ryzen 5 or better, 4 GB minimum (8 GB recommended)
- **GPU:** optional NVIDIA CUDA GPU for faster inference
- **Camera:** any USB or built-in webcam
- **Storage:** ~2 GB for PyTorch and models

---

## 🛠️ Troubleshooting

| Problem                       | Fix                                                                                   |
|-------------------------------|---------------------------------------------------------------------------------------|
| No person detected            | Improve lighting, stand fully in frame, confirm the model loaded in the console       |
| Wrong posture classification  | Keep the full body visible and hold each posture clearly before transitioning         |
| False fall alerts             | Raise the acceleration threshold (default 300) in `fall_logic.py`                     |
| Missed falls                  | Lower the acceleration threshold                                                      |
| Emails not sending            | Check `EMAIL_USER` / `EMAIL_PASS` in `.env`, use a Gmail App Password, check internet |

---

## ⚠️ Limitations & Future Work

- Single fixed camera view; accuracy depends on lighting and camera angle
- Rule-based thresholds may need tuning per environment
- Possible extensions: multi-person tracking, SMS/WhatsApp/Telegram alerts, learned classifier on keypoint sequences, edge deployment (Raspberry Pi / Jetson), mobile app

> This project is a prototype for academic and demonstration purposes. It is **not** a certified medical device and should not be the only safeguard for someone's safety.

---

## 👤 Author

**Kishore** — [@kishore1126](https://github.com/kishore1126)

If you found this useful, consider giving the repo a ⭐
