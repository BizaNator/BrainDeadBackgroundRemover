@echo off
echo ============================================
echo BrainDead Background Remover - Build Script
echo ============================================
echo.

REM Check if venv exists
if not exist "build_env\Scripts\activate.bat" (
    echo [*] Creating isolated virtual environment...
    python -m venv build_env
    if errorlevel 1 (
        echo [!] Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate venv
echo [*] Activating virtual environment...
call build_env\Scripts\activate.bat

REM Install dependencies in isolated env
echo [*] Installing dependencies in isolated environment...
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

REM Build executable
echo.
echo [*] Building portable executable...
pyinstaller --onefile --windowed --name BrainDeadBGRemover ^
    --hidden-import rembg ^
    --hidden-import onnxruntime ^
    --hidden-import PIL._tkinter_finder ^
    --collect-all rembg ^
    --collect-data tkinterdnd2 ^
    bg_remover.py

REM Deactivate venv
call deactivate

REM Copy to root
if exist dist\BrainDeadBGRemover.exe (
    copy /Y dist\BrainDeadBGRemover.exe .
    echo.
    echo ============================================
    echo SUCCESS! BrainDeadBGRemover.exe created
    echo ============================================
    echo.
    echo The executable is fully portable.
    echo You can delete the build_env folder after building.
) else (
    echo.
    echo [!] Build may have failed. Check output above.
)

pause
