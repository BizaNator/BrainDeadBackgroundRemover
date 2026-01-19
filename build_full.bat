@echo off
echo ============================================
echo BrainDead Background Remover - FULL Build
echo (Includes SAM3 with PyTorch/CUDA)
echo ============================================
echo.
echo WARNING: This build includes SAM3 and will be LARGE (~2-3GB)
echo For the lightweight CPU-only version, use build.bat instead.
echo.
pause

REM Check if venv exists
if not exist "build_env_full\Scripts\activate.bat" (
    echo [*] Creating isolated virtual environment...
    python -m venv build_env_full
    if errorlevel 1 (
        echo [!] Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate venv
echo [*] Activating virtual environment...
call build_env_full\Scripts\activate.bat

REM Install dependencies in isolated env
echo [*] Installing base dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo [*] Installing PyTorch with CUDA...
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126

echo [*] Installing SAM3...
pip install sam3

echo [*] Installing PyInstaller...
pip install pyinstaller

REM Build executable
echo.
echo [*] Building portable executable (this may take a while)...
pyinstaller --onefile --windowed --name BrainDeadBGRemover_Full ^
    --hidden-import rembg ^
    --hidden-import onnxruntime ^
    --hidden-import PIL._tkinter_finder ^
    --hidden-import torch ^
    --hidden-import torchvision ^
    --hidden-import sam3 ^
    --collect-all rembg ^
    --collect-all sam3 ^
    --collect-data tkinterdnd2 ^
    bg_remover.py

REM Deactivate venv
call deactivate

REM Copy to root
if exist dist\BrainDeadBGRemover_Full.exe (
    copy /Y dist\BrainDeadBGRemover_Full.exe .
    echo.
    echo ============================================
    echo SUCCESS! BrainDeadBGRemover_Full.exe created
    echo ============================================
    echo.
    echo This version includes SAM3 for text-based segmentation.
    echo Note: File size will be ~2-3GB due to PyTorch/CUDA.
) else (
    echo.
    echo [!] Build may have failed. Check output above.
)

pause
