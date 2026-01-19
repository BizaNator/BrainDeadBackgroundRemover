"""
Main application window - UI setup and event handling.
"""

import os
import sys
import re
import threading
from pathlib import Path
from typing import Optional, List

import tkinter as tk
from tkinter import ttk, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk

try:
    from core.constants import (
        REMBG_MODELS, SUFFIX_OPTIONS, BACKGROUND_OPTIONS,
        VALID_EXTENSIONS, WINDOW_WIDTH, WINDOW_HEIGHT,
        MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT, PREVIEW_MAX_WIDTH, PREVIEW_MAX_HEIGHT
    )
    from core.config import load_config, save_config, set_hf_token, get_hf_token
    from processors.rembg_processor import RembgProcessor
    from processors.sam3_processor import Sam3Processor, is_sam3_available, get_sam3_import_error
    from utils.gpu import check_nvidia_gpu
    from utils.image import auto_crop_image, add_sticker_outline, create_checkerboard_preview, apply_background_color
    from ui.dialogs import show_sam3_install_dialog, show_hf_token_dialog, run_sam3_installation
except ImportError:
    from ..core.constants import (
        REMBG_MODELS, SUFFIX_OPTIONS, BACKGROUND_OPTIONS,
        VALID_EXTENSIONS, WINDOW_WIDTH, WINDOW_HEIGHT,
        MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT, PREVIEW_MAX_WIDTH, PREVIEW_MAX_HEIGHT
    )
    from ..core.config import load_config, save_config, set_hf_token, get_hf_token
    from ..processors.rembg_processor import RembgProcessor
    from ..processors.sam3_processor import Sam3Processor, is_sam3_available, get_sam3_import_error
    from ..utils.gpu import check_nvidia_gpu
    from ..utils.image import auto_crop_image, add_sticker_outline, create_checkerboard_preview, apply_background_color
    from .dialogs import show_sam3_install_dialog, show_hf_token_dialog, run_sam3_installation


class BackgroundRemoverApp:
    """Main application class."""

    def __init__(self):
        self.root = TkinterDnD.Tk()
        self.root.title("\U0001F9E0 BrainDead Background Remover")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        # Load config
        self.config = load_config()

        # Initialize processors
        self.rembg_processor = RembgProcessor()
        self.sam3_processor = Sam3Processor()

        # Processing state
        self.processing = False
        self.current_image_path: Optional[str] = None
        self.image_queue: List[str] = []
        self.bulk_processing = False
        self.last_result_image: Optional[Image.Image] = None

        # Bulk processing stats
        self.bulk_total = 0
        self.bulk_completed = 0
        self.bulk_errors = 0

        # Setup UI
        self._setup_ui()

        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_ui(self):
        """Setup the user interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(
            main_frame,
            text="\U0001F9E0 BrainDead Background Remover",
            font=("Segoe UI", 14, "bold")
        ).pack(pady=(0, 10))

        # Drop zone
        self._setup_drop_zone(main_frame)

        # Status and progress
        self._setup_status(main_frame)

        # Mode selection
        self._setup_mode_selection(main_frame)

        # SAM3 settings (hidden initially unless SAM3 mode)
        self._setup_sam3_settings(main_frame)

        # Standard settings
        self._setup_settings(main_frame)

        # Buttons
        self._setup_buttons(main_frame)

        # Info labels
        self._setup_info(main_frame)

    def _setup_drop_zone(self, parent):
        """Setup the drag-and-drop zone."""
        self.drop_frame = tk.Frame(
            parent,
            bg="#2d2d2d",
            highlightbackground="#4a9eff",
            highlightthickness=2,
            cursor="hand2"
        )
        self.drop_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Drop zone label
        self.drop_label = tk.Label(
            self.drop_frame,
            text="Drop Image(s) Here\n\nor click to browse\n\n(supports bulk processing)",
            font=("Segoe UI", 12),
            bg="#2d2d2d",
            fg="#ffffff",
            pady=40
        )
        self.drop_label.pack(expand=True, fill=tk.BOTH)

        # Preview container (hidden initially)
        self.preview_container = tk.Frame(self.drop_frame, bg="#2d2d2d")
        self.preview_label = tk.Label(self.preview_container, bg="#2d2d2d")
        self.preview_label.pack(side=tk.LEFT, padx=5, expand=True)
        self.result_label = tk.Label(self.preview_container, bg="#2d2d2d")
        self.result_label.pack(side=tk.LEFT, padx=5, expand=True)

        # Enable drag and drop
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self._on_drop)
        self.drop_frame.dnd_bind('<<DragEnter>>', self._on_drag_enter)
        self.drop_frame.dnd_bind('<<DragLeave>>', self._on_drag_leave)

        # Click to browse
        self.drop_frame.bind("<Button-1>", self._browse_file)
        self.drop_label.bind("<Button-1>", self._browse_file)

    def _setup_status(self, parent):
        """Setup status label and progress bar."""
        self.status_var = tk.StringVar(value="Ready - Drop an image to remove background")
        self.status_label = ttk.Label(
            parent,
            textvariable=self.status_var,
            font=("Segoe UI", 9)
        )
        self.status_label.pack(pady=5)

        self.progress = ttk.Progressbar(parent, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=5)

    def _setup_mode_selection(self, parent):
        """Setup Auto/SAM3 mode selection."""
        mode_frame = ttk.LabelFrame(parent, text="Mode", padding="5")
        mode_frame.pack(fill=tk.X, pady=5)

        self.mode_var = tk.StringVar(value="sam3" if self.config.get("use_sam3") else "auto")

        # Auto mode
        ttk.Radiobutton(
            mode_frame,
            text="Auto (rembg) - Automatic background removal",
            variable=self.mode_var,
            value="auto",
            command=self._on_mode_change
        ).pack(anchor=tk.W)

        # SAM3 mode row
        sam3_row = ttk.Frame(mode_frame)
        sam3_row.pack(fill=tk.X, anchor=tk.W)

        sam3_available = is_sam3_available()
        self.sam3_radio = ttk.Radiobutton(
            sam3_row,
            text="SAM3 Text Prompt - Segment by description",
            variable=self.mode_var,
            value="sam3",
            command=self._on_mode_change,
            state=tk.NORMAL if sam3_available else tk.DISABLED
        )
        self.sam3_radio.pack(side=tk.LEFT)

        # Install/Token button
        if not sam3_available:
            ttk.Button(
                sam3_row,
                text="Install SAM3",
                command=self._show_sam3_install_dialog,
                width=12
            ).pack(side=tk.LEFT, padx=(10, 0))
        else:
            ttk.Button(
                sam3_row,
                text="HF Token",
                command=self._show_hf_token_dialog,
                width=10
            ).pack(side=tk.LEFT, padx=(10, 0))

    def _setup_sam3_settings(self, parent):
        """Setup SAM3-specific settings."""
        self.sam3_frame = ttk.LabelFrame(parent, text="SAM3 Text Prompt", padding="5")

        # Text prompt
        prompt_frame = ttk.Frame(self.sam3_frame)
        prompt_frame.pack(fill=tk.X, pady=2)
        ttk.Label(prompt_frame, text="Describe what to segment:").pack(anchor=tk.W)

        self.prompt_var = tk.StringVar(value=self.config.get("sam3_prompt", ""))
        self.prompt_entry = ttk.Entry(prompt_frame, textvariable=self.prompt_var, width=50)
        self.prompt_entry.pack(fill=tk.X, pady=2)
        self.prompt_entry.bind("<KeyRelease>", self._on_setting_change)

        ttk.Label(
            self.sam3_frame,
            text="Examples: 'person', 'car', 'dog', 'red shoes', 'the coffee mug'",
            font=("Segoe UI", 8),
            foreground="gray"
        ).pack(anchor=tk.W)

        # Keep/Remove toggle
        action_frame = ttk.Frame(self.sam3_frame)
        action_frame.pack(fill=tk.X, pady=5)

        self.keep_subject_var = tk.BooleanVar(value=self.config.get("sam3_keep_subject", True))
        ttk.Radiobutton(
            action_frame,
            text="Keep matched object (remove background)",
            variable=self.keep_subject_var,
            value=True,
            command=self._on_setting_change
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            action_frame,
            text="Remove matched object (keep background)",
            variable=self.keep_subject_var,
            value=False,
            command=self._on_setting_change
        ).pack(anchor=tk.W)

        # Show if SAM3 mode is active
        if self.config.get("use_sam3") and is_sam3_available():
            self.sam3_frame.pack(fill=tk.X, pady=5)

    def _setup_settings(self, parent):
        """Setup standard settings panel."""
        settings_frame = ttk.LabelFrame(parent, text="Settings", padding="5")
        settings_frame.pack(fill=tk.X, pady=5)

        # Model selection
        self.model_frame = ttk.Frame(settings_frame)
        self.model_frame.pack(fill=tk.X, pady=2)
        ttk.Label(self.model_frame, text="Model:").pack(side=tk.LEFT)

        self.model_var = tk.StringVar(value=self.config["model"])
        self.model_combo = ttk.Combobox(
            self.model_frame,
            textvariable=self.model_var,
            values=list(REMBG_MODELS.keys()),
            state="readonly",
            width=25
        )
        self.model_combo.pack(side=tk.LEFT, padx=(10, 0))
        self.model_combo.bind("<<ComboboxSelected>>", self._on_model_change)

        # Model description
        self.model_desc_var = tk.StringVar(value=REMBG_MODELS.get(self.config["model"], ""))
        self.model_desc_label = ttk.Label(
            settings_frame,
            textvariable=self.model_desc_var,
            font=("Segoe UI", 8),
            foreground="gray"
        )
        self.model_desc_label.pack(anchor=tk.W, pady=(0, 5))

        # Hide if SAM3 mode
        if self.config.get("use_sam3"):
            self.model_frame.pack_forget()
            self.model_desc_label.pack_forget()

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
        self.suffix_combo.bind("<<ComboboxSelected>>", self._on_setting_change)
        self.suffix_combo.bind("<KeyRelease>", self._on_setting_change)

        # Background color
        bg_frame = ttk.Frame(settings_frame)
        bg_frame.pack(fill=tk.X, pady=2)
        ttk.Label(bg_frame, text="Background:").pack(side=tk.LEFT)

        self.bg_color_var = tk.StringVar(value=self.config.get("background", "transparent"))
        self.bg_combo = ttk.Combobox(
            bg_frame,
            textvariable=self.bg_color_var,
            values=list(BACKGROUND_OPTIONS.keys()),
            state="readonly",
            width=15
        )
        self.bg_combo.pack(side=tk.LEFT, padx=(10, 0))
        self.bg_combo.bind("<<ComboboxSelected>>", self._on_setting_change)

        # Background preview
        bg_color = BACKGROUND_OPTIONS.get(self.config.get("background", "transparent"), (None, None))[1]
        preview_color = "#ffffff" if bg_color == (255, 255, 255) else "#000000" if bg_color == (0, 0, 0) else "#cccccc"
        self.bg_preview = tk.Label(bg_frame, text="    ", bg=preview_color, relief="sunken", width=3)
        self.bg_preview.pack(side=tk.LEFT, padx=(5, 0))

        # Alpha matting
        self.alpha_var = tk.BooleanVar(value=self.config["alpha_matting"])
        self.alpha_check = ttk.Checkbutton(
            settings_frame,
            text="Alpha Matting (better edges, slower)",
            variable=self.alpha_var,
            command=self._on_alpha_toggle
        )
        self.alpha_check.pack(anchor=tk.W, pady=5)

        # Alpha settings frame
        self.alpha_settings_frame = ttk.Frame(settings_frame)
        if self.config["alpha_matting"] and not self.config.get("use_sam3"):
            self.alpha_settings_frame.pack(fill=tk.X, pady=5, padx=(20, 0))

        self._setup_alpha_sliders()

        # Hide alpha in SAM3 mode
        if self.config.get("use_sam3"):
            self.alpha_check.pack_forget()
            self.alpha_settings_frame.pack_forget()

        # Auto-crop
        self.autocrop_var = tk.BooleanVar(value=self.config.get("auto_crop", False))
        self.autocrop_check = ttk.Checkbutton(
            settings_frame,
            text="Auto-crop to object (center with margin)",
            variable=self.autocrop_var,
            command=self._on_autocrop_toggle
        )
        self.autocrop_check.pack(anchor=tk.W, pady=5)

        # Auto-crop margin
        self.autocrop_settings_frame = ttk.Frame(settings_frame)
        if self.config.get("auto_crop", False):
            self.autocrop_settings_frame.pack(fill=tk.X, pady=5, padx=(20, 0))

        margin_frame = ttk.Frame(self.autocrop_settings_frame)
        margin_frame.pack(fill=tk.X, pady=2)
        ttk.Label(margin_frame, text="Margin (px):").pack(side=tk.LEFT)
        self.margin_var = tk.IntVar(value=self.config.get("auto_crop_margin", 10))
        ttk.Scale(
            margin_frame, from_=0, to=100,
            variable=self.margin_var, orient=tk.HORIZONTAL, length=150
        ).pack(side=tk.LEFT, padx=10)
        ttk.Label(margin_frame, textvariable=self.margin_var, width=4).pack(side=tk.LEFT)

        # Sticker mode
        self.sticker_var = tk.BooleanVar(value=self.config.get("sticker_mode", False))
        self.sticker_check = ttk.Checkbutton(
            settings_frame,
            text="Sticker mode (colored outline)",
            variable=self.sticker_var,
            command=self._on_sticker_toggle
        )
        self.sticker_check.pack(anchor=tk.W, pady=5)

        # Sticker settings
        self.sticker_settings_frame = ttk.Frame(settings_frame)
        if self.config.get("sticker_mode", False):
            self.sticker_settings_frame.pack(fill=tk.X, pady=5, padx=(20, 0))

        self._setup_sticker_settings()

    def _setup_alpha_sliders(self):
        """Setup alpha matting sliders."""
        # FG threshold
        fg_frame = ttk.Frame(self.alpha_settings_frame)
        fg_frame.pack(fill=tk.X, pady=2)
        ttk.Label(fg_frame, text="FG Threshold:").pack(side=tk.LEFT)
        self.fg_threshold_var = tk.IntVar(value=self.config["alpha_matting_fg_threshold"])
        ttk.Scale(
            fg_frame, from_=200, to=255,
            variable=self.fg_threshold_var, orient=tk.HORIZONTAL, length=150
        ).pack(side=tk.LEFT, padx=10)
        ttk.Label(fg_frame, textvariable=self.fg_threshold_var, width=4).pack(side=tk.LEFT)

        # BG threshold
        bg_frame = ttk.Frame(self.alpha_settings_frame)
        bg_frame.pack(fill=tk.X, pady=2)
        ttk.Label(bg_frame, text="BG Threshold:").pack(side=tk.LEFT)
        self.bg_threshold_var = tk.IntVar(value=self.config["alpha_matting_bg_threshold"])
        ttk.Scale(
            bg_frame, from_=0, to=50,
            variable=self.bg_threshold_var, orient=tk.HORIZONTAL, length=150
        ).pack(side=tk.LEFT, padx=10)
        ttk.Label(bg_frame, textvariable=self.bg_threshold_var, width=4).pack(side=tk.LEFT)

        # Erode size
        erode_frame = ttk.Frame(self.alpha_settings_frame)
        erode_frame.pack(fill=tk.X, pady=2)
        ttk.Label(erode_frame, text="Erode Size:").pack(side=tk.LEFT)
        self.erode_var = tk.IntVar(value=self.config["alpha_matting_erode_size"])
        ttk.Scale(
            erode_frame, from_=0, to=40,
            variable=self.erode_var, orient=tk.HORIZONTAL, length=150
        ).pack(side=tk.LEFT, padx=10)
        ttk.Label(erode_frame, textvariable=self.erode_var, width=4).pack(side=tk.LEFT)

    def _setup_sticker_settings(self):
        """Setup sticker mode settings."""
        # Outline width
        width_frame = ttk.Frame(self.sticker_settings_frame)
        width_frame.pack(fill=tk.X, pady=2)
        ttk.Label(width_frame, text="Outline width:").pack(side=tk.LEFT)
        self.sticker_width_var = tk.IntVar(value=self.config.get("sticker_width", 5))
        ttk.Scale(
            width_frame, from_=1, to=20,
            variable=self.sticker_width_var, orient=tk.HORIZONTAL, length=150
        ).pack(side=tk.LEFT, padx=10)
        ttk.Label(width_frame, textvariable=self.sticker_width_var, width=4).pack(side=tk.LEFT)

        # Outline color
        color_frame = ttk.Frame(self.sticker_settings_frame)
        color_frame.pack(fill=tk.X, pady=2)
        ttk.Label(color_frame, text="Outline color:").pack(side=tk.LEFT)

        self.sticker_color_var = tk.StringVar(value=self.config.get("sticker_color", "#ffffff"))

        # Color presets
        color_presets = [
            ("#ffffff", "White"),
            ("#000000", "Black"),
            ("#ff0000", "Red"),
            ("#00ff00", "Green"),
            ("#0000ff", "Blue"),
            ("#ffff00", "Yellow"),
        ]

        for color, name in color_presets:
            btn = tk.Button(
                color_frame,
                bg=color,
                width=2,
                height=1,
                relief="raised",
                command=lambda c=color: self._set_sticker_color(c)
            )
            btn.pack(side=tk.LEFT, padx=2)

        # Custom color button
        ttk.Button(
            color_frame,
            text="...",
            width=3,
            command=self._choose_sticker_color
        ).pack(side=tk.LEFT, padx=5)

        # Color preview
        self.sticker_color_preview = tk.Label(
            color_frame,
            text="    ",
            bg=self.sticker_color_var.get(),
            relief="sunken",
            width=4
        )
        self.sticker_color_preview.pack(side=tk.LEFT, padx=5)

    def _setup_buttons(self, parent):
        """Setup action buttons."""
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=10)

        self.process_btn = ttk.Button(
            btn_frame,
            text="Process Image",
            command=self._process_current_image,
            state=tk.DISABLED
        )
        self.process_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Open Output Folder",
            command=self._open_output_folder
        ).pack(side=tk.LEFT, padx=5)

    def _setup_info(self, parent):
        """Setup info labels at bottom."""
        info_frame = ttk.Frame(parent)
        info_frame.pack(side=tk.BOTTOM, fill=tk.X)

        ttk.Label(
            info_frame,
            text="Supports: PNG, JPG, JPEG, WEBP, BMP, TIFF",
            font=("Segoe UI", 8),
            foreground="gray"
        ).pack(side=tk.LEFT)

        # SAM3 status
        sam3_available = is_sam3_available()
        sam3_error = get_sam3_import_error()

        if sam3_available:
            sam3_status = "SAM3: Ready"
            sam3_color = "green"
        else:
            has_gpu, gpu_name = check_nvidia_gpu()
            if sam3_error and "sam3" not in sam3_error.lower():
                sam3_status = f"SAM3: Error - {sam3_error[:30]}"
                sam3_color = "red"
            elif has_gpu:
                sam3_status = f"SAM3: Not installed (GPU: {gpu_name[:20] if gpu_name else 'detected'})"
                sam3_color = "orange"
            else:
                sam3_status = "SAM3: Not installed (No NVIDIA GPU)"
                sam3_color = "gray"

        ttk.Label(
            info_frame,
            text=sam3_status,
            font=("Segoe UI", 8),
            foreground=sam3_color
        ).pack(side=tk.RIGHT)

    # Event handlers

    def _on_drag_enter(self, event):
        self.drop_frame.config(highlightbackground="#00ff00", highlightthickness=3)

    def _on_drag_leave(self, event):
        self.drop_frame.config(highlightbackground="#4a9eff", highlightthickness=2)

    def _on_drop(self, event):
        self.drop_frame.config(highlightbackground="#4a9eff", highlightthickness=2)

        # Parse dropped files - Windows TkinterDnD formats:
        # - Paths with spaces: {C:/path/to file.png} {C:/another path.png}
        # - Paths without spaces: C:/path/file.png C:/path/file2.png
        # - Mixed: {C:/path with space/file.png} C:/simple/path.png
        data = event.data
        file_paths = []

        # First, extract any paths in curly braces (paths with spaces)
        if '{' in data:
            # Find all {path} entries
            braced_paths = re.findall(r'\{([^}]+)\}', data)
            file_paths.extend([p.strip() for p in braced_paths])
            # Remove braced entries from data to handle remaining paths
            data = re.sub(r'\{[^}]+\}', '', data).strip()

        # Handle remaining paths (space-separated or newline-separated)
        if data:
            if '\n' in data:
                remaining = [p.strip() for p in data.split('\n') if p.strip()]
            else:
                # Space-separated paths - need to be careful with this
                remaining = [p.strip() for p in data.split() if p.strip()]
            file_paths.extend(remaining)

        # Normalize paths - handle URL encoding and path separators
        normalized_paths = []
        for fp in file_paths:
            # Handle URL-style encoding (%20 for space, etc.)
            try:
                from urllib.parse import unquote
                fp = unquote(fp)
            except:
                pass
            # Normalize path separators
            fp = os.path.normpath(fp)
            normalized_paths.append(fp)

        # Filter valid images
        valid_files = [
            fp for fp in normalized_paths
            if Path(fp).exists() and Path(fp).suffix.lower() in VALID_EXTENSIONS
        ]

        if not valid_files:
            self.status_var.set(f"Error: No valid image files found")
            return

        if len(valid_files) == 1:
            self._load_image(valid_files[0])
        else:
            self._start_bulk_processing(valid_files)

    def _browse_file(self, event=None):
        file_paths = filedialog.askopenfilenames(
            title="Select Image(s)",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.tif"),
                ("PNG", "*.png"),
                ("JPEG", "*.jpg *.jpeg"),
                ("WebP", "*.webp"),
                ("All files", "*.*")
            ]
        )
        if file_paths:
            if len(file_paths) == 1:
                self._load_image(file_paths[0])
            else:
                self._start_bulk_processing(list(file_paths))

    def _load_image(self, file_path: str):
        path = Path(file_path)

        if not path.exists():
            self.status_var.set("Error: File not found")
            return

        if path.suffix.lower() not in VALID_EXTENSIONS:
            self.status_var.set(f"Error: Unsupported format {path.suffix}")
            return

        self.current_image_path = file_path
        self.last_result_image = None

        try:
            img = Image.open(file_path)
            img.thumbnail((PREVIEW_MAX_WIDTH, PREVIEW_MAX_HEIGHT), Image.Resampling.LANCZOS)

            photo = ImageTk.PhotoImage(img)

            self.drop_label.pack_forget()
            self.preview_container.pack_forget()

            self.preview_label.config(image=photo)
            self.preview_label.image = photo

            self.result_label.config(image='')
            self.result_label.image = None

            self.preview_container.pack(expand=True, fill=tk.BOTH, pady=10)

            orig_img = Image.open(file_path)
            self.status_var.set(f"Loaded: {path.name} ({orig_img.width}x{orig_img.height})")

            self.process_btn.config(state=tk.NORMAL)

            # Auto-process
            if self.config.get("auto_process", True):
                if self.mode_var.get() == "sam3":
                    if self.prompt_var.get().strip():
                        self._process_current_image()
                    else:
                        self.status_var.set(f"Loaded: {path.name} - Enter a prompt to process")
                else:
                    self._process_current_image()

        except Exception as e:
            self.status_var.set(f"Error loading image: {e}")

    def _on_mode_change(self):
        use_sam3 = self.mode_var.get() == "sam3"

        if use_sam3:
            self.sam3_frame.pack(fill=tk.X, pady=5, after=self.progress)
            self.model_frame.pack_forget()
            self.model_desc_label.pack_forget()
            self.alpha_check.pack_forget()
            self.alpha_settings_frame.pack_forget()
        else:
            self.sam3_frame.pack_forget()
            self.model_frame.pack(fill=tk.X, pady=2)
            self.model_desc_label.pack(anchor=tk.W, pady=(0, 5))
            self.alpha_check.pack(anchor=tk.W, pady=5)
            if self.alpha_var.get():
                self.alpha_settings_frame.pack(fill=tk.X, pady=5, padx=(20, 0))

        self._save_current_config()

    def _on_model_change(self, event=None):
        model = self.model_var.get()
        self.model_desc_var.set(REMBG_MODELS.get(model, ""))
        self.rembg_processor.clear_session()
        self._save_current_config()

    def _on_setting_change(self, event=None):
        # Update background preview
        bg_choice = self.bg_color_var.get()
        bg_color = BACKGROUND_OPTIONS.get(bg_choice, (None, None))[1]
        if bg_color == (255, 255, 255):
            preview_color = "#ffffff"
        elif bg_color == (0, 0, 0):
            preview_color = "#000000"
        else:
            preview_color = "#cccccc"
        self.bg_preview.config(bg=preview_color)
        self._save_current_config()

    def _on_alpha_toggle(self):
        if self.alpha_var.get():
            self.alpha_settings_frame.pack(fill=tk.X, pady=5, padx=(20, 0))
        else:
            self.alpha_settings_frame.pack_forget()
        self._save_current_config()

    def _on_autocrop_toggle(self):
        if self.autocrop_var.get():
            self.autocrop_settings_frame.pack(fill=tk.X, pady=5, padx=(20, 0))
        else:
            self.autocrop_settings_frame.pack_forget()
        self._save_current_config()

    def _on_sticker_toggle(self):
        if self.sticker_var.get():
            self.sticker_settings_frame.pack(fill=tk.X, pady=5, padx=(20, 0))
        else:
            self.sticker_settings_frame.pack_forget()
        self._save_current_config()

    def _set_sticker_color(self, color: str):
        self.sticker_color_var.set(color)
        self.sticker_color_preview.config(bg=color)
        self._save_current_config()

    def _choose_sticker_color(self):
        from tkinter import colorchooser
        color = colorchooser.askcolor(
            initialcolor=self.sticker_color_var.get(),
            title="Choose Outline Color"
        )
        if color[1]:
            self._set_sticker_color(color[1])

    def _show_sam3_install_dialog(self):
        show_sam3_install_dialog(
            self.root,
            self.config,
            lambda: run_sam3_installation(self.config, self.status_var.set)
        )

    def _show_hf_token_dialog(self):
        def on_save(token: str):
            self.config["hf_token"] = token
            save_config(self.config)
            if token:
                set_hf_token(token)
                self.sam3_processor.clear_model()
            self.status_var.set("Token saved. Restart may be required.")

        show_hf_token_dialog(self.root, self.config, on_save)

    # Processing

    def _process_current_image(self):
        if not self.current_image_path or self.processing:
            return

        if self.mode_var.get() == "sam3":
            if not self.prompt_var.get().strip():
                self.status_var.set("Error: Please enter a text prompt for SAM3")
                return

        self.processing = True
        self.process_btn.config(state=tk.DISABLED)
        self.progress.start(10)
        self.status_var.set("Processing... (first run downloads model)")

        thread = threading.Thread(target=self._process_image_thread)
        thread.daemon = True
        thread.start()

    def _process_image_thread(self):
        try:
            input_path = Path(self.current_image_path)
            suffix = self.suffix_var.get() or "_nobg"
            output_path = input_path.parent / f"{input_path.stem}{suffix}.png"

            # Build options
            options = self._build_processing_options()

            # Process
            if self.mode_var.get() == "sam3":
                result = self.sam3_processor.process(
                    input_path, output_path, options,
                    lambda msg: self.root.after(0, lambda: self.status_var.set(msg))
                )
            else:
                result = self.rembg_processor.process(
                    input_path, output_path, options,
                    lambda msg: self.root.after(0, lambda: self.status_var.set(msg))
                )

            # Post-process
            result = self._apply_post_processing(result)

            # Apply background and save
            bg_choice = self.bg_color_var.get()
            bg_color = BACKGROUND_OPTIONS.get(bg_choice, (None, None))[1]
            final = apply_background_color(result, bg_color)
            final.save(output_path, "PNG")

            self.root.after(0, lambda: self._on_process_complete(output_path))

        except Exception as e:
            import traceback
            error_msg = str(e) if str(e) else type(e).__name__
            print(f"Processing error: {error_msg}")
            traceback.print_exc()
            self.root.after(0, lambda err=error_msg: self._on_process_error(err))

    def _build_processing_options(self) -> dict:
        """Build options dict for processors."""
        return {
            "model": self.model_var.get(),
            "alpha_matting": self.alpha_var.get(),
            "alpha_matting_foreground_threshold": self.fg_threshold_var.get(),
            "alpha_matting_background_threshold": self.bg_threshold_var.get(),
            "alpha_matting_erode_size": self.erode_var.get(),
            "prompt": self.prompt_var.get().strip(),
            "keep_subject": self.keep_subject_var.get(),
            "hf_token": self.config.get("hf_token", ""),
        }

    def _apply_post_processing(self, image: Image.Image) -> Image.Image:
        """Apply post-processing effects (crop, sticker)."""
        result = image

        # Auto-crop
        if self.autocrop_var.get():
            margin = self.margin_var.get()
            result = auto_crop_image(result, margin)

        # Sticker mode
        if self.sticker_var.get():
            width = self.sticker_width_var.get()
            color_hex = self.sticker_color_var.get()
            # Convert hex to RGB
            color = tuple(int(color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
            result = add_sticker_outline(result, width, color)

        return result

    def _on_process_complete(self, output_path: Path):
        self.processing = False
        self.progress.stop()
        self.process_btn.config(state=tk.NORMAL)
        self.status_var.set(f"Saved: {output_path.name}")

        # Show result preview
        try:
            result_img = Image.open(output_path)
            self.last_result_image = result_img.copy()

            result_preview = create_checkerboard_preview(
                result_img,
                (PREVIEW_MAX_WIDTH, PREVIEW_MAX_HEIGHT)
            )

            result_photo = ImageTk.PhotoImage(result_preview)
            self.result_label.config(image=result_photo)
            self.result_label.image = result_photo
        except Exception as e:
            print(f"Error showing result preview: {e}")

        # Flash success
        self.drop_frame.config(highlightbackground="#00ff00")
        self.root.after(1000, lambda: self.drop_frame.config(highlightbackground="#4a9eff"))

    def _on_process_error(self, error: str):
        self.processing = False
        self.progress.stop()
        self.process_btn.config(state=tk.NORMAL)
        self.status_var.set(f"Error: {error}")
        self.drop_frame.config(highlightbackground="#ff0000")
        self.root.after(1000, lambda: self.drop_frame.config(highlightbackground="#4a9eff"))

    # Bulk processing

    def _start_bulk_processing(self, file_paths: List[str]):
        if self.mode_var.get() == "sam3":
            if not self.prompt_var.get().strip():
                self.status_var.set(f"Enter a SAM3 prompt first, then drop {len(file_paths)} images")
                self.image_queue = file_paths
                return

        self.image_queue = file_paths.copy()
        self.bulk_processing = True
        self.bulk_total = len(file_paths)
        self.bulk_completed = 0
        self.bulk_errors = 0

        self.process_btn.config(state=tk.DISABLED)
        self.status_var.set(f"Bulk processing: 0/{self.bulk_total} images...")

        self.preview_label.pack_forget()
        self.drop_label.config(text=f"Processing {self.bulk_total} images...\n\n0/{self.bulk_total} completed")
        self.drop_label.pack(expand=True, fill=tk.BOTH)

        self.progress.start(10)
        self._process_next_in_queue()

    def _process_next_in_queue(self):
        if not self.image_queue:
            self._on_bulk_complete()
            return

        if self.processing:
            self.root.after(100, self._process_next_in_queue)
            return

        file_path = self.image_queue.pop(0)
        self.current_image_path = file_path

        self.status_var.set(f"Processing: {Path(file_path).name} ({self.bulk_completed + 1}/{self.bulk_total})")
        self.drop_label.config(text=f"Processing {self.bulk_total} images...\n\n{self.bulk_completed}/{self.bulk_total} completed")

        self.processing = True
        thread = threading.Thread(target=self._process_bulk_image_thread, args=(file_path,))
        thread.daemon = True
        thread.start()

    def _process_bulk_image_thread(self, file_path: str):
        try:
            input_path = Path(file_path)
            suffix = self.suffix_var.get() or "_nobg"
            output_path = input_path.parent / f"{input_path.stem}{suffix}.png"

            options = self._build_processing_options()

            if self.mode_var.get() == "sam3":
                result = self.sam3_processor.process(input_path, output_path, options)
            else:
                result = self.rembg_processor.process(input_path, output_path, options)

            result = self._apply_post_processing(result)

            bg_choice = self.bg_color_var.get()
            bg_color = BACKGROUND_OPTIONS.get(bg_choice, (None, None))[1]
            final = apply_background_color(result, bg_color)
            final.save(output_path, "PNG")

            self.bulk_completed += 1
            self.root.after(0, self._on_bulk_item_complete)

        except Exception as e:
            self.bulk_errors += 1
            self.bulk_completed += 1
            self.root.after(0, lambda: self._on_bulk_item_error(file_path, str(e)))

    def _on_bulk_item_complete(self):
        self.processing = False
        self.drop_label.config(text=f"Processing {self.bulk_total} images...\n\n{self.bulk_completed}/{self.bulk_total} completed")
        self._process_next_in_queue()

    def _on_bulk_item_error(self, file_path: str, error: str):
        self.processing = False
        print(f"Error processing {file_path}: {error}")
        self._process_next_in_queue()

    def _on_bulk_complete(self):
        self.bulk_processing = False
        self.processing = False
        self.progress.stop()
        self.process_btn.config(state=tk.NORMAL)

        if self.bulk_errors > 0:
            msg = f"Completed: {self.bulk_completed - self.bulk_errors}/{self.bulk_total} images ({self.bulk_errors} errors)"
        else:
            msg = f"Completed: {self.bulk_total} images processed successfully!"

        self.status_var.set(msg)
        self.drop_label.config(text=f"Done!\n\n{msg}\n\nDrop more images to continue")
        self.current_image_path = None

    def _open_output_folder(self):
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

    def _save_current_config(self):
        self.config.update({
            "model": self.model_var.get(),
            "suffix": self.suffix_var.get(),
            "background": self.bg_color_var.get(),
            "alpha_matting": self.alpha_var.get(),
            "alpha_matting_fg_threshold": self.fg_threshold_var.get(),
            "alpha_matting_bg_threshold": self.bg_threshold_var.get(),
            "alpha_matting_erode_size": self.erode_var.get(),
            "use_sam3": self.mode_var.get() == "sam3",
            "sam3_prompt": self.prompt_var.get(),
            "sam3_keep_subject": self.keep_subject_var.get(),
            "auto_crop": self.autocrop_var.get(),
            "auto_crop_margin": self.margin_var.get(),
            "sticker_mode": self.sticker_var.get(),
            "sticker_color": self.sticker_color_var.get(),
            "sticker_width": self.sticker_width_var.get(),
        })
        save_config(self.config)

    def _on_close(self):
        self._save_current_config()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
