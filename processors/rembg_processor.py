"""
Rembg processor - CPU-based background removal using rembg library.
"""

import io
from pathlib import Path
from PIL import Image
from typing import Optional, Callable

from rembg import remove, new_session

from .base import BaseProcessor


class RembgProcessor(BaseProcessor):
    """Background removal using rembg with various ONNX models."""

    def __init__(self):
        self._session = None
        self._current_model = None

    def process(
        self,
        input_path: Path,
        output_path: Path,
        options: dict,
        status_callback: Optional[Callable[[str], None]] = None
    ) -> Image.Image:
        """
        Process image using rembg.

        Options:
            model: str - rembg model name
            alpha_matting: bool - enable alpha matting
            alpha_matting_foreground_threshold: int
            alpha_matting_background_threshold: int
            alpha_matting_erode_size: int
        """
        model = options.get("model", "birefnet-general")

        # Get or create session
        if self._session is None or self._current_model != model:
            if status_callback:
                status_callback(f"Loading model: {model}...")
            self._session = new_session(model)
            self._current_model = model

        # Read input image
        with open(input_path, 'rb') as f:
            input_data = f.read()

        # Build kwargs
        if status_callback:
            status_callback("Removing background...")

        kwargs = {
            "session": self._session,
        }

        if options.get("alpha_matting", False):
            kwargs["alpha_matting"] = True
            kwargs["alpha_matting_foreground_threshold"] = options.get(
                "alpha_matting_foreground_threshold", 240
            )
            kwargs["alpha_matting_background_threshold"] = options.get(
                "alpha_matting_background_threshold", 10
            )
            kwargs["alpha_matting_erode_size"] = options.get(
                "alpha_matting_erode_size", 10
            )

        output_data = remove(input_data, **kwargs)

        # Load the processed image
        output_img = Image.open(io.BytesIO(output_data)).convert("RGBA")

        return output_img

    def is_available(self) -> bool:
        """Rembg is always available (it's a required dependency)."""
        return True

    def get_name(self) -> str:
        return "rembg"

    def clear_session(self) -> None:
        """Clear the cached model session."""
        self._session = None
        self._current_model = None
