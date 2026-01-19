"""
GPU detection and CUDA version utilities.
"""

import sys
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple


def check_nvidia_gpu() -> Tuple[bool, Optional[str]]:
    """
    Check if an NVIDIA GPU is available.

    Returns:
        Tuple of (has_gpu, gpu_name)
    """
    # Common nvidia-smi locations on Windows
    nvidia_smi_paths = [
        "nvidia-smi",  # If in PATH
        r"C:\Windows\System32\nvidia-smi.exe",
        r"C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe",
    ]

    for nvidia_smi in nvidia_smi_paths:
        try:
            result = subprocess.run(
                [nvidia_smi, "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            if result.returncode == 0 and result.stdout.strip():
                return True, result.stdout.strip().split('\n')[0]
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError, Exception):
            continue

    # Try checking via torch if available
    try:
        import torch
        if torch.cuda.is_available():
            return True, torch.cuda.get_device_name(0)
    except ImportError:
        pass

    return False, None


def get_recommended_cuda_version(gpu_name: Optional[str]) -> Tuple[str, str]:
    """
    Get recommended CUDA/PyTorch version based on GPU architecture.

    Args:
        gpu_name: Name of the detected GPU

    Returns:
        Tuple of (cuda_version, pytorch_index_url)

    Notes:
        - RTX 50 series (Blackwell, sm_120): Needs cu130
        - RTX 40/30/20 series and older: cu126 works fine
    """
    if gpu_name:
        gpu_upper = gpu_name.upper()
        # RTX 50 series (5090, 5080, 5070, etc.) - Blackwell architecture
        if "RTX 50" in gpu_upper or "5090" in gpu_upper or "5080" in gpu_upper or "5070" in gpu_upper:
            return "13.0", "https://download.pytorch.org/whl/cu130"

    # Default to cu126 for older GPUs (RTX 40/30/20, GTX, etc.)
    return "12.6", "https://download.pytorch.org/whl/cu126"


def get_app_venv_path() -> Optional[Path]:
    """Get the path to the app's virtual environment Python executable."""
    if getattr(sys, 'frozen', False):
        base_path = Path(sys.executable).parent
    else:
        base_path = Path(__file__).parent.parent

    # Check for venv in app directory
    venv_path = base_path / "venv"
    if venv_path.exists():
        if sys.platform == 'win32':
            return venv_path / "Scripts" / "python.exe"
        else:
            return venv_path / "bin" / "python"
    return None


def get_python_executable() -> Optional[str]:
    """Get the Python executable path for installing packages."""
    # If running from source (not frozen exe), always use the current interpreter
    # This ensures we install into the same venv we're running from
    if not getattr(sys, 'frozen', False):
        return sys.executable

    # Frozen exe - try to find app's venv first
    venv_python = get_app_venv_path()
    if venv_python and venv_python.exists():
        return str(venv_python)

    # Fallback to system Python
    python_paths = [
        shutil.which("python"),
        shutil.which("python3"),
        os.path.expanduser("~\\AppData\\Local\\Programs\\Python\\Python312\\python.exe"),
        os.path.expanduser("~\\AppData\\Local\\Programs\\Python\\Python311\\python.exe"),
    ]
    for p in python_paths:
        if p and os.path.exists(p):
            return p
    return None
