#!/usr/bin/env python
"""
SYSTEM VERIFICATION SCRIPT
Checks if all dependencies and files are ready for presentation
"""

import os
import sys
import importlib.util

def check_file(filename, description=""):
    """Check if a file exists."""
    exists = os.path.exists(filename)
    status = "✅" if exists else "❌"
    print(f"{status} {filename:30} {'- ' + description if description else ''}")
    return exists

def check_import(module_name, pip_name=""):
    """Check if a Python module can be imported."""
    try:
        importlib.import_module(module_name)
        print(f"✅ {module_name:30} (import works)")
        return True
    except ImportError:
        pip_name = pip_name or module_name
        print(f"❌ {module_name:30} (NOT installed)")
        print(f"   Fix: pip install {pip_name}")
        return False

def main():
    print("\n" + "="*70)
    print("  FALL DETECTION SYSTEM - PRE-PRESENTATION VERIFICATION")
    print("="*70 + "\n")
    
    # Check Python version
    print("📍 Python Version Check:")
    python_version = sys.version_info
    if python_version.major >= 3 and python_version.minor >= 8:
        print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro} (OK)")
    else:
        print(f"❌ Python {python_version.major}.{python_version.minor} (Need 3.8+)")
    
    # Check project files
    print("\n📁 Project Files:")
    files_ok = all([
        check_file("app.py", "Flask web server"),
        check_file("camera.py", "Video camera + YOLO pipeline"),
        check_file("fall_logic.py", "Fall detection logic (260+ lines)"),
        check_file("models.py", "Database models"),
        check_file("email_service.py", "Email alerts"),
        check_file("yolov8n-pose.pt", "YOLOv8 model weights (3.2MB)"),
        check_file("requirements.txt", "Python dependencies"),
        check_file("DEMO_ALL_STATES.py", "Automated test"),
        check_file("run_live_demo.py", "Live webcam demo"),
    ])
    
    # Check Python packages
    print("\n📦 Python Dependencies:")
    packages_ok = all([
        check_import("flask", "flask"),
        check_import("cv2", "opencv-python"),
        check_import("ultralytics", "ultralytics"),
        check_import("torch", "torch"),
        check_import("numpy", "numpy"),
        check_import("sqlalchemy", "sqlalchemy"),
    ])
    
    # Check database
    print("\n🗄️  Database Setup:")
    db_exists = os.path.exists("instance/fall_detection.db")
    if db_exists:
        print("✅ Database exists (instance/fall_detection.db)")
    else:
        print("⚠️  Database not created yet")
        print("   Note: Flask will create it on first run")
    
    # Check templates
    print("\n🎨 Web Templates:")
    templates_ok = all([
        check_file("templates/base.html", "Base template"),
        check_file("templates/login.html", "Login page"),
        check_file("templates/register.html", "Registration page"),
        check_file("templates/dashboard.html", "Main dashboard"),
    ])
    
    # Summary
    print("\n" + "="*70)
    print("  VERIFICATION SUMMARY")
    print("="*70 + "\n")
    
    if files_ok and packages_ok:
        print("✅ ALL SYSTEMS READY FOR PRESENTATION!\n")
        
        print("🚀 NEXT STEPS:")
        print("   1. Run automated test:")
        print("      python DEMO_ALL_STATES.py\n")
        
        print("   2. Run live demo (with webcam):")
        print("      python run_live_demo.py\n")
        
        print("   3. (Optional) Start web app:")
        print("      python app.py")
        print("      Then open: http://localhost:5000\n")
        
        print("📖 Reference:")
        print("   • Read: PROJECT_REVIEW_GUIDE.md")
        print("   • Read: DEMO_COMMANDS.txt\n")
        
        return 0
    else:
        print("⚠️  MISSING COMPONENTS DETECTED\n")
        
        if not files_ok:
            print("📁 Missing Files:")
            print("   Ensure all project files are present in current directory\n")
        
        if not packages_ok:
            print("📦 Missing Python Packages:")
            print("   Run: pip install -r requirements.txt\n")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
