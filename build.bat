@echo off
echo ============================================
echo BrainDead Background Remover - Build Script
echo ============================================

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

REM Build executable
echo.
echo Building portable executable...
pyinstaller --onefile --windowed --name BrainDeadBGRemover ^
    --hidden-import rembg ^
    --hidden-import onnxruntime ^
    --hidden-import PIL._tkinter_finder ^
    --collect-all rembg ^
    --collect-data tkinterdnd2 ^
    bg_remover.py

REM Copy to root
if exist dist\BrainDeadBGRemover.exe (
    copy /Y dist\BrainDeadBGRemover.exe .
    echo.
    echo ============================================
    echo SUCCESS! BrainDeadBGRemover.exe created
    echo ============================================
) else (
    echo.
    echo Build may have failed. Check output above.
)

pause
