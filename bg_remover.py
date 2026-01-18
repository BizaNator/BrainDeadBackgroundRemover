"""
BrainDead Background Remover
A lightweight, portable drag-and-drop background removal utility.
Uses rembg with BiRefNet and other models for high-quality results.
"""

import os
import sys
import json
import threading
from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk
import io

# Import rembg
from rembg import remove, new_session

# Available models with descriptions
MODELS = {
    "birefnet-general": "BiRefNet General - Best quality, most accurate",
    "birefnet-general-lite": "BiRefNet Lite - Faster, good quality",
    "birefnet-portrait": "BiRefNet Portrait - Optimized for faces",
    "birefnet-dis": "BiRefNet DIS - Dichotomous segmentation",
    "birefnet-hrsod": "BiRefNet HRSOD - High-res salient objects",
    "birefnet-cod": "BiRefNet COD - Concealed object detection",
    "birefnet-massive": "BiRefNet Massive - Large dataset trained",
    "u2net": "U2Net - Classic model, balanced",
    "u2netp": "U2Net-P - Lightweight, fast",
    "u2net_human_seg": "U2Net Human - Human segmentation",
    "u2net_cloth_seg": "U2Net Cloth - Clothing segmentation",
    "isnet-general-use": "ISNet General - Good all-around",
    "isnet-anime": "ISNet Anime - Anime/illustration optimized",
    "sam": "SAM - Segment Anything Model",
}

# Output suffix options
SUFFIX_OPTIONS = [
    "_nobg",
    "_alpha",
    "_masked",
    "_transparent",
    "_cutout",
]

# Config file path (next to executable or script)
def get_config_path():
    if getattr(sys, 'frozen', False):
        base_path = Path(sys.executable).parent
    else:
        base_path = Path(__file__).parent
    return base_path / "bg_remover_config.json"


def load_config():
    """Load configuration from file."""
    config_path = get_config_path()
    default_config = {
        "model": "birefnet-general",
        "suffix": "_nobg",
        "alpha_matting": False,
        "alpha_matting_fg_threshold": 240,
        "alpha_matting_bg_threshold": 10,
        "alpha_matting_erode_size": 10,
        "output_format": "png",
        "auto_process": True,
    }

    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                saved = json.load(f)
                default_config.update(saved)
        except Exception:
            pass

    return default_config


def save_config(config):
    """Save configuration to file."""
    config_path = get_config_path()
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Failed to save config: {e}")


class BackgroundRemoverApp:
    def __init__(self):
        self.root = TkinterDnD.Tk()
        self.root.title("BrainDead Background Remover")
        self.root.geometry("500x600")
        self.root.minsize(400, 500)

        # Load config
        self.config = load_config()

        # Session cache for faster processing
        self.session = None
        self.current_model = None

        # Processing state
        self.processing = False
        self.current_image_path = None

        # Setup UI
        self.setup_ui()

        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ui(self):
        """Setup the user interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="🧠 BrainDead Background Remover",
            font=("Segoe UI", 14, "bold")
        )
        title_label.pack(pady=(0, 10))

        # Drop zone frame
        self.drop_frame = tk.Frame(
            main_frame,
            bg="#2d2d2d",
            highlightbackground="#4a9eff",
            highlightthickness=2,
            cursor="hand2"
        )
        self.drop_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Drop zone content
        self.drop_label = tk.Label(
            self.drop_frame,
            text="🖼️ Drop Image Here\n\nor click to browse",
            font=("Segoe UI", 12),
            bg="#2d2d2d",
            fg="#ffffff",
            pady=40
        )
        self.drop_label.pack(expand=True, fill=tk.BOTH)

        # Preview label (hidden initially)
        self.preview_label = tk.Label(self.drop_frame, bg="#2d2d2d")

        # Enable drag and drop
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.on_drop)
        self.drop_frame.dnd_bind('<<DragEnter>>', self.on_drag_enter)
        self.drop_frame.dnd_bind('<<DragLeave>>', self.on_drag_leave)

        # Click to browse
        self.drop_frame.bind("<Button-1>", self.browse_file)
        self.drop_label.bind("<Button-1>", self.browse_file)

        # Status label
        self.status_var = tk.StringVar(value="Ready - Drop an image to remove background")
        self.status_label = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            font=("Segoe UI", 9)
        )
        self.status_label.pack(pady=5)

        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=5)

        # Settings frame
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
        settings_frame.pack(fill=tk.X, pady=10)

        # Model selection
        model_frame = ttk.Frame(settings_frame)
        model_frame.pack(fill=tk.X, pady=2)
        ttk.Label(model_frame, text="Model:").pack(side=tk.LEFT)

        self.model_var = tk.StringVar(value=self.config["model"])
        self.model_combo = ttk.Combobox(
            model_frame,
            textvariable=self.model_var,
            values=list(MODELS.keys()),
            state="readonly",
            width=25
        )
        self.model_combo.pack(side=tk.LEFT, padx=(10, 0))
        self.model_combo.bind("<<ComboboxSelected>>", self.on_model_change)

        # Model description
        self.model_desc_var = tk.StringVar(value=MODELS.get(self.config["model"], ""))
        self.model_desc_label = ttk.Label(
            settings_frame,
            textvariable=self.model_desc_var,
            font=("Segoe UI", 8),
            foreground="gray"
        )
        self.model_desc_label.pack(anchor=tk.W, pady=(0, 5))

        # Suffix selection
        suffix_frame = ttk.Frame(settings_frame)
        suffix_frame.pack(fill=tk.X, pady=2)
        ttk.Label(suffix_frame, text="Output suffix:").pack(side=tk.LEFT)

        self.suffix_var = tk.StringVar(value=self.config["suffix"])
        self.suffix_combo = ttk.Combobox(
            suffix_frame,
            textvariable=self.suffix_var,
            values=SUFFIX_OPTIONS,
            width=15
        )
        self.suffix_combo.pack(side=tk.LEFT, padx=(10, 0))
        self.suffix_combo.bind("<<ComboboxSelected>>", self.on_setting_change)
        self.suffix_combo.bind("<KeyRelease>", self.on_setting_change)

        # Alpha matting checkbox
        self.alpha_var = tk.BooleanVar(value=self.config["alpha_matting"])
        alpha_check = ttk.Checkbutton(
            settings_frame,
            text="Alpha Matting (better edges, slower)",
            variable=self.alpha_var,
            command=self.on_alpha_toggle
        )
        alpha_check.pack(anchor=tk.W, pady=5)

        # Alpha matting settings (collapsible)
        self.alpha_settings_frame = ttk.Frame(settings_frame)
        if self.config["alpha_matting"]:
            self.alpha_settings_frame.pack(fill=tk.X, pady=5, padx=(20, 0))

        # Foreground threshold
        fg_frame = ttk.Frame(self.alpha_settings_frame)
        fg_frame.pack(fill=tk.X, pady=2)
        ttk.Label(fg_frame, text="FG Threshold:").pack(side=tk.LEFT)
        self.fg_threshold_var = tk.IntVar(value=self.config["alpha_matting_fg_threshold"])
        fg_scale = ttk.Scale(
            fg_frame,
            from_=200,
            to=255,
            variable=self.fg_threshold_var,
            orient=tk.HORIZONTAL,
            length=150
        )
        fg_scale.pack(side=tk.LEFT, padx=10)
        ttk.Label(fg_frame, textvariable=self.fg_threshold_var, width=4).pack(side=tk.LEFT)

        # Background threshold
        bg_frame = ttk.Frame(self.alpha_settings_frame)
        bg_frame.pack(fill=tk.X, pady=2)
        ttk.Label(bg_frame, text="BG Threshold:").pack(side=tk.LEFT)
        self.bg_threshold_var = tk.IntVar(value=self.config["alpha_matting_bg_threshold"])
        bg_scale = ttk.Scale(
            bg_frame,
            from_=0,
            to=50,
            variable=self.bg_threshold_var,
            orient=tk.HORIZONTAL,
            length=150
        )
        bg_scale.pack(side=tk.LEFT, padx=10)
        ttk.Label(bg_frame, textvariable=self.bg_threshold_var, width=4).pack(side=tk.LEFT)

        # Erode size
        erode_frame = ttk.Frame(self.alpha_settings_frame)
        erode_frame.pack(fill=tk.X, pady=2)
        ttk.Label(erode_frame, text="Erode Size:").pack(side=tk.LEFT)
        self.erode_var = tk.IntVar(value=self.config["alpha_matting_erode_size"])
        erode_scale = ttk.Scale(
            erode_frame,
            from_=0,
            to=40,
            variable=self.erode_var,
            orient=tk.HORIZONTAL,
            length=150
        )
        erode_scale.pack(side=tk.LEFT, padx=10)
        ttk.Label(erode_frame, textvariable=self.erode_var, width=4).pack(side=tk.LEFT)

        # Buttons frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        self.process_btn = ttk.Button(
            btn_frame,
            text="Process Image",
            command=self.process_current_image,
            state=tk.DISABLED
        )
        self.process_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Open Output Folder",
            command=self.open_output_folder
        ).pack(side=tk.LEFT, padx=5)

        # Info label
        info_label = ttk.Label(
            main_frame,
            text="Supports: PNG, JPG, JPEG, WEBP, BMP, TIFF",
            font=("Segoe UI", 8),
            foreground="gray"
        )
        info_label.pack(side=tk.BOTTOM)

    def on_drag_enter(self, event):
        """Visual feedback when dragging over."""
        self.drop_frame.config(highlightbackground="#00ff00", highlightthickness=3)

    def on_drag_leave(self, event):
        """Reset visual feedback."""
        self.drop_frame.config(highlightbackground="#4a9eff", highlightthickness=2)

    def on_drop(self, event):
        """Handle dropped files."""
        self.drop_frame.config(highlightbackground="#4a9eff", highlightthickness=2)

        # Parse dropped file path
        file_path = event.data

        # Handle Windows paths with curly braces
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]

        # Handle multiple files - take first one
        if '\n' in file_path:
            file_path = file_path.split('\n')[0]

        # Clean up path
        file_path = file_path.strip()

        self.load_image(file_path)

    def browse_file(self, event=None):
        """Open file browser dialog."""
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.tif"),
                ("PNG", "*.png"),
                ("JPEG", "*.jpg *.jpeg"),
                ("WebP", "*.webp"),
                ("All files", "*.*")
            ]
        )

        if file_path:
            self.load_image(file_path)

    def load_image(self, file_path: str):
        """Load and preview an image."""
        # Validate file
        valid_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.tif'}
        path = Path(file_path)

        if not path.exists():
            self.status_var.set(f"Error: File not found")
            return

        if path.suffix.lower() not in valid_extensions:
            self.status_var.set(f"Error: Unsupported format {path.suffix}")
            return

        self.current_image_path = file_path

        # Show preview
        try:
            img = Image.open(file_path)
            img.thumbnail((300, 200), Image.Resampling.LANCZOS)

            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)

            # Update preview
            self.drop_label.pack_forget()
            self.preview_label.config(image=photo)
            self.preview_label.image = photo  # Keep reference
            self.preview_label.pack(expand=True)

            # Update status
            orig_img = Image.open(file_path)
            self.status_var.set(f"Loaded: {path.name} ({orig_img.width}x{orig_img.height})")

            # Enable process button
            self.process_btn.config(state=tk.NORMAL)

            # Auto-process if enabled
            if self.config.get("auto_process", True):
                self.process_current_image()

        except Exception as e:
            self.status_var.set(f"Error loading image: {e}")

    def process_current_image(self):
        """Process the currently loaded image."""
        if not self.current_image_path or self.processing:
            return

        self.processing = True
        self.process_btn.config(state=tk.DISABLED)
        self.progress.start(10)
        self.status_var.set("Processing... (first run downloads model)")

        # Run in thread to keep UI responsive
        thread = threading.Thread(target=self._process_image_thread)
        thread.daemon = True
        thread.start()

    def _process_image_thread(self):
        """Background thread for image processing."""
        try:
            input_path = Path(self.current_image_path)

            # Build output path
            suffix = self.suffix_var.get() or "_nobg"
            output_path = input_path.parent / f"{input_path.stem}{suffix}.png"

            # Get or create session
            model = self.model_var.get()
            if self.session is None or self.current_model != model:
                self.root.after(0, lambda: self.status_var.set(f"Loading model: {model}..."))
                self.session = new_session(model)
                self.current_model = model

            # Read input image
            with open(input_path, 'rb') as f:
                input_data = f.read()

            # Process
            self.root.after(0, lambda: self.status_var.set("Removing background..."))

            # Build kwargs
            kwargs = {
                "session": self.session,
            }

            if self.alpha_var.get():
                kwargs["alpha_matting"] = True
                kwargs["alpha_matting_foreground_threshold"] = self.fg_threshold_var.get()
                kwargs["alpha_matting_background_threshold"] = self.bg_threshold_var.get()
                kwargs["alpha_matting_erode_size"] = self.erode_var.get()

            output_data = remove(input_data, **kwargs)

            # Save output
            with open(output_path, 'wb') as f:
                f.write(output_data)

            # Update UI on main thread
            self.root.after(0, lambda: self._on_process_complete(output_path))

        except Exception as e:
            self.root.after(0, lambda: self._on_process_error(str(e)))

    def _on_process_complete(self, output_path: Path):
        """Called when processing completes successfully."""
        self.processing = False
        self.progress.stop()
        self.process_btn.config(state=tk.NORMAL)
        self.status_var.set(f"Saved: {output_path.name}")

        # Show success notification
        self.drop_frame.config(highlightbackground="#00ff00")
        self.root.after(1000, lambda: self.drop_frame.config(highlightbackground="#4a9eff"))

    def _on_process_error(self, error: str):
        """Called when processing fails."""
        self.processing = False
        self.progress.stop()
        self.process_btn.config(state=tk.NORMAL)
        self.status_var.set(f"Error: {error}")
        self.drop_frame.config(highlightbackground="#ff0000")
        self.root.after(1000, lambda: self.drop_frame.config(highlightbackground="#4a9eff"))

    def on_model_change(self, event=None):
        """Handle model selection change."""
        model = self.model_var.get()
        self.model_desc_var.set(MODELS.get(model, ""))
        self.session = None  # Force reload on next process
        self.save_current_config()

    def on_setting_change(self, event=None):
        """Handle settings change."""
        self.save_current_config()

    def on_alpha_toggle(self):
        """Handle alpha matting toggle."""
        if self.alpha_var.get():
            self.alpha_settings_frame.pack(fill=tk.X, pady=5, padx=(20, 0))
        else:
            self.alpha_settings_frame.pack_forget()
        self.save_current_config()

    def save_current_config(self):
        """Save current settings to config file."""
        self.config.update({
            "model": self.model_var.get(),
            "suffix": self.suffix_var.get(),
            "alpha_matting": self.alpha_var.get(),
            "alpha_matting_fg_threshold": self.fg_threshold_var.get(),
            "alpha_matting_bg_threshold": self.bg_threshold_var.get(),
            "alpha_matting_erode_size": self.erode_var.get(),
        })
        save_config(self.config)

    def open_output_folder(self):
        """Open the output folder in file explorer."""
        if self.current_image_path:
            folder = Path(self.current_image_path).parent
        else:
            folder = Path.cwd()

        if sys.platform == 'win32':
            os.startfile(folder)
        elif sys.platform == 'darwin':
            os.system(f'open "{folder}"')
        else:
            os.system(f'xdg-open "{folder}"')

    def on_close(self):
        """Handle window close."""
        self.save_current_config()
        self.root.destroy()

    def run(self):
        """Start the application."""
        self.root.mainloop()


def main():
    app = BackgroundRemoverApp()
    app.run()


if __name__ == "__main__":
    main()
