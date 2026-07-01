@echo off
setlocal enabledelayedexpansion

echo ======================================================
echo ELDER GUARD MANUAL GPU INSTALLER (FIXED)
echo ======================================================
echo.

:: Path to virtual environment python
set "PYTHON_EXE=%~dp0venv\Scripts\python.exe"

if not exist "!PYTHON_EXE!" (
    echo [ERROR] Virtual environment Python not found at: !PYTHON_EXE!
    pause
    exit /b
)

:: 1. Upgrade PIP (Crucial for handling modern .whl files)
echo [1/4] Upgrading pip to handle modern wheel files...
"!PYTHON_EXE!" -m pip install --upgrade pip

:: 2. Uninstall broken versions
echo [2/4] Removing old PyTorch...
"!PYTHON_EXE!" -m pip uninstall -y torch torchvision torchaudio 2>nul

:: 3. Install from manual downloads
echo [3/4] Checking for manual download files...
if exist "torch-2.5.1+cu124-cp39-cp39-win_amd64.whl" (
    echo Found files! Installing locally...
    "!PYTHON_EXE!" -m pip install "torch-2.5.1+cu124-cp39-cp39-win_amd64.whl" "torchvision-0.20.1+cu124-cp39-cp39-win_amd64.whl" "torchaudio-2.5.1+cu124-cp39-cp39-win_amd64.whl" --no-cache-dir
) else (
    echo [ERROR] Could not find the .whl files in: %~dp0
    echo Please ensure the filenames match exactly.
    pause
    exit /b
)

:: 4. Verification
echo.
echo ======================================================
echo [4/4] FINAL GPU STATUS CHECK
echo ======================================================
"!PYTHON_EXE!" -c "import torch; print('CUDA is available: ' + str(torch.cuda.is_available())); print('PyTorch Device: ' + torch.cuda.get_device_name(0)) if torch.cuda.is_available() else print('STILL NO GPU DETECTED.')"

echo.
if %errorlevel% neq 0 (
    echo.
    echo [CRITICAL ERROR] The wheel file is still showing as 'invalid'.
    echo This almost always means the 2.5GB download was corrupted or incomplete.
    echo.
    echo PLEASE CHECK: 
    echo Right-click 'torch-2.5.1+cu124-cp39-cp39-win_amd64.whl' -> Properties.
    echo It MUST be approximately 2.50 GB (2,684,354,560 bytes).
    echo If it is smaller, please re-download it.
) else (
    echo [SUCCESS] Your RTX 4050 is now fully active!
)

pause
