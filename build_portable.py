"""
Build script to create a portable executable.
Run: python build_portable.py
"""

import subprocess
import sys
import shutil
from pathlib import Path


def main():
    print("=" * 60)
    print("BrainDead Background Remover - Portable Build Script")
    print("=" * 60)

    # Check for PyInstaller
    try:
        import PyInstaller
        print(f"[OK] PyInstaller {PyInstaller.__version__} found")
    except ImportError:
        print("[!] Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Build command
    script_dir = Path(__file__).parent
    main_script = script_dir / "bg_remover.py"

    print("\n[*] Building portable executable...")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "BrainDeadBGRemover",
        "--icon", "NONE",  # No icon, or specify .ico file
        "--add-data", f"{get_tkdnd_path()};tkdnd",
        "--hidden-import", "rembg",
        "--hidden-import", "onnxruntime",
        "--hidden-import", "PIL",
        "--hidden-import", "tkinterdnd2",
        "--collect-all", "rembg",
        "--collect-all", "onnxruntime",
        str(main_script)
    ]

    # Try simpler build first
    cmd_simple = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "BrainDeadBGRemover",
        # Core dependencies
        "--hidden-import", "rembg",
        "--hidden-import", "onnxruntime",
        "--hidden-import", "PIL._tkinter_finder",
        # App modules (modular structure)
        "--hidden-import", "core",
        "--hidden-import", "core.constants",
        "--hidden-import", "core.config",
        "--hidden-import", "processors",
        "--hidden-import", "processors.base",
        "--hidden-import", "processors.rembg_processor",
        "--hidden-import", "processors.sam3_processor",
        "--hidden-import", "ui",
        "--hidden-import", "ui.main_window",
        "--hidden-import", "ui.dialogs",
        "--hidden-import", "utils",
        "--hidden-import", "utils.gpu",
        "--hidden-import", "utils.image",
        # Data collection
        "--collect-all", "rembg",
        "--collect-data", "tkinterdnd2",
        str(main_script)
    ]

    try:
        subprocess.check_call(cmd_simple)
        print("\n[OK] Build complete!")
        print(f"[OK] Executable: {script_dir / 'dist' / 'BrainDeadBGRemover.exe'}")
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Build failed: {e}")
        print("\nTry manual build with:")
        print("  pyinstaller --onefile --windowed bg_remover.py")
        return 1

    # Copy to root for convenience
    dist_exe = script_dir / "dist" / "BrainDeadBGRemover.exe"
    if dist_exe.exists():
        final_exe = script_dir / "BrainDeadBGRemover.exe"
        shutil.copy2(dist_exe, final_exe)
        print(f"[OK] Copied to: {final_exe}")

    print("\n" + "=" * 60)
    print("NOTES:")
    print("- First run will download the AI model (~170MB for BiRefNet)")
    print("- Models are cached in ~/.u2net/")
    print("- The exe is fully portable - just copy it anywhere!")
    print("=" * 60)

    return 0


def get_tkdnd_path():
    """Get path to tkdnd library."""
    try:
        import tkinterdnd2
        return str(Path(tkinterdnd2.__file__).parent / "tkdnd")
    except:
        return "tkdnd"


if __name__ == "__main__":
    sys.exit(main())
