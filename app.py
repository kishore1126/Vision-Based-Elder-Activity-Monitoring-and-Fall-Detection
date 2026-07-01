from flask import Flask, render_template, Response, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, FallLog
from camera import VideoCamera
import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env

app = Flask(__name__)
# Email configuration: SMTP server/credentials come from environment variables;
# the recipient is either the logged-in user or ?user_email= query parameter.
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'secret-key-goes-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite')

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)
# Global camera variable
camera_instance = None

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    # redirect to login, legacy behaviour
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Login Failed. Check credentials.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.')
            return redirect(url_for('register'))
        
        new_user = User(email=email, name=name, password=generate_password_hash(password, method='pbkdf2:sha256'))
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', name=current_user.name, email=current_user.email)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

def gen(camera):
    print("Streaming generator started.")
    while True:
        frame = camera.get_frame_bytes()
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        # Very small sleep to yield control to other threads
        import time
        time.sleep(0.001)

@app.route('/video_feed')
@login_required
def video_feed():
    global camera_instance
    # Always use the currently logged-in user's email for alerts
    req_email = current_user.email
    
    if camera_instance is None:
        print(f"Initializing camera for user: {req_email}")
        camera_instance = VideoCamera(app, req_email)
    else:
        # Update destination email without restarting whole system
        print(f"Ensuring alert recipient is set to: {req_email}")
        camera_instance.user_email = req_email

    return Response(gen(camera_instance),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
@login_required
def get_status():
    global camera_instance
    status = "Unknown"
    device = "None"
    details = {"angle": 0, "state": "None", "is_fall": False}
    if camera_instance:
        status = getattr(camera_instance, 'current_status', "Unknown")
        details = getattr(camera_instance, 'current_details', details)
        device = getattr(camera_instance, 'device_name', "Unknown")
    
    return {'status': status, 'details': details, 'device': device}

@app.route('/history')
@login_required
def get_history():
    logs = FallLog.query.order_by(FallLog.timestamp.desc()).limit(10).all()
    return {'logs': [{'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'), 'status': log.status} for log in logs]}

if __name__ == '__main__':
    print("Starting app...")
    try:
        with app.app_context():
            print("Creating database tables...")
            db.create_all()
            print("Database created.")
        print("Running app...")
        print(" * Running on http://127.0.0.1:5000")
        app.run(debug=True, use_reloader=False, threaded=True) 
    except Exception as e:
        print(f"Error starting app: {e}")
        import traceback
        traceback.print_exc()
