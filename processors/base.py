"""
Base processor interface - defines the contract for all image processors.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from PIL import Image
from typing import Optional, Callable


class BaseProcessor(ABC):
    """Abstract base class for image processing backends."""

    @abstractmethod
    def process(
        self,
        input_path: Path,
        output_path: Path,
        options: dict,
        status_callback: Optional[Callable[[str], None]] = None
    ) -> Image.Image:
        """
        Process an image to remove/modify background.

        Args:
            input_path: Path to input image
            output_path: Path for output image
            options: Processing options dict
            status_callback: Optional callback for status updates

        Returns:
            Processed PIL Image (RGBA)
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this processor is available (dependencies installed)."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get the display name of this processor."""
        pass
