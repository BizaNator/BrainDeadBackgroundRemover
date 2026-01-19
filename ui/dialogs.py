"""
Dialog windows - SAM3 installation, HF token configuration, etc.
"""

import sys
import subprocess
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional

try:
    from core.config import get_config_path, save_config, set_hf_token
    from utils.gpu import check_nvidia_gpu, get_recommended_cuda_version, get_python_executable
except ImportError:
    from ..core.config import get_config_path, save_config, set_hf_token
    from ..utils.gpu import check_nvidia_gpu, get_recommended_cuda_version, get_python_executable


def show_sam3_install_dialog(
    parent: tk.Tk,
    config: dict,
    on_install: Callable[[], None]
) -> None:
    """
    Show dialog to install SAM3 with GPU check and HF token setup.

    Args:
        parent: Parent window
        config: Current configuration dict
        on_install: Callback to run installation
    """
    has_gpu, gpu_name = check_nvidia_gpu()
    cuda_version, pytorch_index_url = get_recommended_cuda_version(gpu_name)

    # Create dialog window
    dialog = tk.Toplevel(parent)
    dialog.title("Install SAM3")
    dialog.geometry("500x520")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()

    # Center the dialog
    dialog.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() - 500) // 2
    y = parent.winfo_y() + (parent.winfo_height() - 520) // 2
    dialog.geometry(f"+{x}+{y}")

    frame = ttk.Frame(dialog, padding="20")
    frame.pack(fill=tk.BOTH, expand=True)

    # Title
    ttk.Label(
        frame,
        text="SAM3 Installation",
        font=("Segoe UI", 12, "bold")
    ).pack(anchor=tk.W)

    ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

    # GPU Status
    gpu_frame = ttk.Frame(frame)
    gpu_frame.pack(fill=tk.X, pady=5)

    if has_gpu:
        gpu_icon = "+"
        gpu_color = "green"
        gpu_text = f"NVIDIA GPU detected: {gpu_name}"
    else:
        gpu_icon = "X"
        gpu_color = "red"
        gpu_text = "No NVIDIA GPU detected"

    ttk.Label(gpu_frame, text=gpu_icon, foreground=gpu_color, font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
    ttk.Label(gpu_frame, text=gpu_text, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(5, 0))

    # Show recommended CUDA version
    if has_gpu:
        cuda_frame = ttk.Frame(frame)
        cuda_frame.pack(fill=tk.X, pady=2)
        ttk.Label(cuda_frame, text="+", foreground="green", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        ttk.Label(cuda_frame, text=f"Will install PyTorch with CUDA {cuda_version}", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(5, 0))

    # Hugging Face Token Section
    ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

    ttk.Label(
        frame,
        text="Hugging Face Access (Required)",
        font=("Segoe UI", 10, "bold")
    ).pack(anchor=tk.W)

    ttk.Label(
        frame,
        text="SAM3 is a gated model. You must:",
        font=("Segoe UI", 9)
    ).pack(anchor=tk.W)

    steps = [
        "1. Create account at huggingface.co (free)",
        "2. Request access at huggingface.co/facebook/sam3",
        "3. Create token at huggingface.co/settings/tokens",
        "4. Paste your token below:",
    ]
    for step in steps:
        ttk.Label(frame, text=step, font=("Segoe UI", 9)).pack(anchor=tk.W, padx=(10, 0))

    # Token entry
    token_frame = ttk.Frame(frame)
    token_frame.pack(fill=tk.X, pady=5)

    current_token = config.get("hf_token", "")
    token_var = tk.StringVar(value=current_token)
    token_entry = ttk.Entry(token_frame, textvariable=token_var, width=50, show="*")
    token_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def toggle_token():
        if token_entry.cget('show') == '*':
            token_entry.config(show='')
            show_btn.config(text="Hide")
        else:
            token_entry.config(show='*')
            show_btn.config(text="Show")

    show_btn = ttk.Button(token_frame, text="Show", width=6, command=toggle_token)
    show_btn.pack(side=tk.LEFT, padx=(5, 0))

    # Token status
    if current_token:
        token_status = ttk.Label(frame, text="Token saved", font=("Segoe UI", 8), foreground="green")
    else:
        token_status = ttk.Label(frame, text="No token configured", font=("Segoe UI", 8), foreground="orange")
    token_status.pack(anchor=tk.W)

    # Warning if no GPU
    if not has_gpu:
        ttk.Label(
            frame,
            text="\nWarning: SAM3 requires an NVIDIA GPU with CUDA.",
            font=("Segoe UI", 9),
            foreground="red"
        ).pack(anchor=tk.W, pady=5)

    # Install command info
    ttk.Label(
        frame,
        text="\nThis will install in a terminal:",
        font=("Segoe UI", 9)
    ).pack(anchor=tk.W)

    ttk.Label(
        frame,
        text="pip install torch torchvision sam3 + huggingface login",
        font=("Consolas", 8),
        foreground="gray"
    ).pack(anchor=tk.W)

    # Buttons
    btn_frame = ttk.Frame(frame)
    btn_frame.pack(fill=tk.X, pady=20)

    def do_install():
        # Save token
        token = token_var.get().strip()
        if token:
            config["hf_token"] = token
            save_config(config)
            set_hf_token(token)
        dialog.destroy()
        on_install()

    if has_gpu:
        install_btn = tk.Button(
            btn_frame,
            text="Install SAM3",
            command=do_install,
            padx=15,
            pady=5
        )
    else:
        install_btn = tk.Button(
            btn_frame,
            text="Install Anyway",
            command=do_install,
            padx=15,
            pady=5
        )
    install_btn.pack(side=tk.LEFT, padx=5)

    cancel_btn = tk.Button(
        btn_frame,
        text="Cancel",
        command=dialog.destroy,
        padx=15,
        pady=5
    )
    cancel_btn.pack(side=tk.LEFT, padx=5)

    # Open HF link button
    def open_hf():
        webbrowser.open("https://huggingface.co/facebook/sam3")

    hf_btn = tk.Button(
        btn_frame,
        text="Open HuggingFace",
        command=open_hf,
        padx=10,
        pady=5
    )
    hf_btn.pack(side=tk.RIGHT, padx=5)


def show_hf_token_dialog(
    parent: tk.Tk,
    config: dict,
    on_save: Callable[[str], None]
) -> None:
    """
    Show dialog to configure Hugging Face token.

    Args:
        parent: Parent window
        config: Current configuration dict
        on_save: Callback with token when saved
    """
    dialog = tk.Toplevel(parent)
    dialog.title("Hugging Face Token")
    dialog.geometry("450x280")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()

    # Center the dialog
    dialog.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() - 450) // 2
    y = parent.winfo_y() + (parent.winfo_height() - 280) // 2
    dialog.geometry(f"+{x}+{y}")

    frame = ttk.Frame(dialog, padding="20")
    frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(
        frame,
        text="Hugging Face Token Configuration",
        font=("Segoe UI", 12, "bold")
    ).pack(anchor=tk.W)

    ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

    ttk.Label(
        frame,
        text="SAM3 requires a Hugging Face token to download the model.",
        font=("Segoe UI", 9)
    ).pack(anchor=tk.W)

    steps = [
        "1. Request access at huggingface.co/facebook/sam3",
        "2. Create token at huggingface.co/settings/tokens",
        "3. Paste your token below:",
    ]
    for step in steps:
        ttk.Label(frame, text=step, font=("Segoe UI", 9)).pack(anchor=tk.W, padx=(10, 0))

    # Token entry
    token_frame = ttk.Frame(frame)
    token_frame.pack(fill=tk.X, pady=10)

    current_token = config.get("hf_token", "")
    token_var = tk.StringVar(value=current_token)
    token_entry = ttk.Entry(token_frame, textvariable=token_var, width=45, show="*")
    token_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def toggle_token():
        if token_entry.cget('show') == '*':
            token_entry.config(show='')
            show_btn.config(text="Hide")
        else:
            token_entry.config(show='*')
            show_btn.config(text="Show")

    show_btn = ttk.Button(token_frame, text="Show", width=6, command=toggle_token)
    show_btn.pack(side=tk.LEFT, padx=(5, 0))

    # Status
    if current_token:
        status_text = "Token is saved"
        status_color = "green"
    else:
        status_text = "No token configured"
        status_color = "orange"

    ttk.Label(frame, text=status_text, font=("Segoe UI", 8), foreground=status_color).pack(anchor=tk.W)

    # Buttons
    btn_frame = ttk.Frame(frame)
    btn_frame.pack(fill=tk.X, pady=15)

    def save_token():
        token = token_var.get().strip()
        dialog.destroy()
        on_save(token)

    tk.Button(btn_frame, text="Save Token", command=save_token, padx=15, pady=5).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Cancel", command=dialog.destroy, padx=15, pady=5).pack(side=tk.LEFT, padx=5)

    def open_hf():
        webbrowser.open("https://huggingface.co/facebook/sam3")

    tk.Button(btn_frame, text="Open HuggingFace", command=open_hf, padx=10, pady=5).pack(side=tk.RIGHT, padx=5)


def run_sam3_installation(config: dict, status_callback: Callable[[str], None]) -> None:
    """
    Run SAM3 installation in a terminal window.

    Args:
        config: Configuration dict containing hf_token
        status_callback: Callback for status updates
    """
    python_exe = get_python_executable()

    # Detect GPU and get recommended CUDA version
    has_gpu, gpu_name = check_nvidia_gpu()
    cuda_version, pytorch_index_url = get_recommended_cuda_version(gpu_name)

    # Get HF token from config
    hf_token = config.get("hf_token", "")

    if not python_exe:
        messagebox.showerror(
            "Python Not Found",
            "Could not find Python installation.\n\n"
            "Please install Python 3.12+ and ensure it's in your PATH,\n"
            "then run manually:\n\n"
            f"pip install torch torchvision --index-url {pytorch_index_url}\n"
            "pip install sam3"
        )
        return

    # Create install script
    script_path = get_config_path().parent / "install_sam3.bat"

    # Build HF login command
    if hf_token:
        hf_login_cmd = f'"{python_exe}" -c "from huggingface_hub import login; login(token=\'{hf_token}\', add_to_git_credential=False)"'
        hf_login_section = f'''
echo.
echo [2/6] Logging into Hugging Face...
{hf_login_cmd}

if errorlevel 1 (
    echo.
    echo [WARNING] Hugging Face login failed. You may need to login manually.
    echo Run: huggingface-cli login
)
'''
    else:
        hf_login_section = '''
echo.
echo [2/6] Hugging Face Login...
echo No token provided. You will need to login manually:
echo   1. Run: huggingface-cli login
echo   2. Or set HF_TOKEN environment variable
echo.
'''

    script_content = f'''@echo off
echo ============================================
echo Installing SAM3 (Text-based Segmentation)
echo ============================================
echo.
echo Python: {python_exe}
echo GPU: {gpu_name if gpu_name else "Not detected"}
echo CUDA version: {cuda_version} (auto-detected for your GPU)
echo.
echo This will install PyTorch with CUDA and SAM3.
echo This may take several minutes...
echo.

echo [1/6] Installing PyTorch with CUDA {cuda_version}...
"{python_exe}" -m pip install torch torchvision --index-url {pytorch_index_url}

if errorlevel 1 (
    echo.
    echo [ERROR] PyTorch installation failed!
    pause
    exit /b 1
)
{hf_login_section}
echo.
echo [3/6] Installing triton (Windows workaround)...
"{python_exe}" -m pip install triton-windows || "{python_exe}" -m pip install triton || echo Triton not available, continuing...

echo.
echo [4/6] Installing SAM3 dependencies (psutil, huggingface_hub)...
"{python_exe}" -m pip install psutil huggingface_hub

echo.
echo [5/6] Installing SAM3...
"{python_exe}" -m pip install sam3

if errorlevel 1 (
    echo.
    echo [ERROR] SAM3 installation failed!
    pause
    exit /b 1
)

echo.
echo [6/6] Downloading SAM3 assets (BPE vocabulary)...
"{python_exe}" -c "import os, urllib.request; assets_dir = os.path.join(os.path.dirname(__import__('sam3').__file__), '..', 'assets'); os.makedirs(assets_dir, exist_ok=True); bpe_file = os.path.join(assets_dir, 'bpe_simple_vocab_16e6.txt.gz'); urllib.request.urlretrieve('https://raw.githubusercontent.com/openai/CLIP/main/clip/bpe_simple_vocab_16e6.txt.gz', bpe_file); print('Downloaded to:', bpe_file)"

if errorlevel 1 (
    echo.
    echo [WARNING] Could not download BPE vocabulary. SAM3 may not work correctly.
    echo You can manually download from: https://raw.githubusercontent.com/openai/CLIP/main/clip/bpe_simple_vocab_16e6.txt.gz
)

echo.
echo ============================================
echo Installation complete!
echo ============================================
echo.
echo IMPORTANT: Make sure you have requested access to the SAM3 model at:
echo   https://huggingface.co/facebook/sam3
echo.
echo Please restart BrainDead Background Remover
echo to enable SAM3 mode.
echo.
pause
'''
    with open(script_path, 'w') as f:
        f.write(script_content)

    # Run the script in a new terminal
    status_callback("Opening installer... Please complete installation in terminal.")

    if sys.platform == 'win32':
        subprocess.Popen(
            ['cmd', '/c', 'start', 'cmd', '/k', str(script_path)],
            shell=True
        )
    else:
        # Linux/Mac
        subprocess.Popen(['bash', str(script_path)])

    messagebox.showinfo(
        "Installation Started",
        "SAM3 installation has started in a new terminal window.\n\n"
        "After installation completes, please restart this application\n"
        "to enable SAM3 mode."
    )
