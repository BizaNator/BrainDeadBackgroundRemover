@echo off
echo ============================================
echo BrainDead Background Remover
echo ============================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo [*] First run - creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [!] Failed to create virtual environment
        pause
        exit /b 1
    )

    echo [*] Installing dependencies...
    call venv\Scripts\activate.bat
    pip install --upgrade pip
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

echo [*] Starting application...
python bg_remover.py

call deactivate
