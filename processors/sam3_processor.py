"""
SAM3 processor - GPU-based text-prompted segmentation using Meta's SAM3.
"""

from pathlib import Path
from PIL import Image
from typing import Optional, Callable, Tuple
import numpy as np

try:
    from processors.base import BaseProcessor
    from core.config import get_hf_token, set_hf_token
except ImportError:
    from .base import BaseProcessor
    from ..core.config import get_hf_token, set_hf_token


# Check for SAM3 availability
SAM3_AVAILABLE = False
SAM3_IMPORT_ERROR = None
try:
    from sam3.model_builder import build_sam3_image_model
    from sam3.model.sam3_image_processor import Sam3Processor as Sam3ProcessorClass
    SAM3_AVAILABLE = True
except ImportError as e:
    SAM3_IMPORT_ERROR = str(e)
except Exception as e:
    SAM3_IMPORT_ERROR = f"Unexpected error: {e}"


class Sam3Processor(BaseProcessor):
    """Text-prompted segmentation using SAM3 (Segment Anything 3)."""

    def __init__(self):
        self._model = None
        self._processor = None

    def process(
        self,
        input_path: Path,
        output_path: Path,
        options: dict,
        status_callback: Optional[Callable[[str], None]] = None
    ) -> Image.Image:
        """
        Process image using SAM3 text-based segmentation.

        Options:
            prompt: str - text describing what to segment
            keep_subject: bool - True to keep matched object, False to remove it
            hf_token: str - Hugging Face token for model access
        """
        if not SAM3_AVAILABLE:
            raise RuntimeError("SAM3 is not installed. Run: pip install sam3")

        # Load model if needed
        if self._model is None:
            if status_callback:
                status_callback("Loading SAM3 model...")
            print("[SAM3] Loading model...")

            # Setup HF token for authentication
            hf_token = options.get("hf_token", "") or get_hf_token()
            if hf_token:
                print("[SAM3] Setting up Hugging Face authentication...")
                set_hf_token(hf_token)

            try:
                self._model = build_sam3_image_model()
                self._processor = Sam3ProcessorClass(self._model)
                print("[SAM3] Model loaded successfully")
            except Exception as e:
                error_msg = str(e)
                print(f"[SAM3] Model loading failed: {error_msg}")

                # Check for gated repo error
                if "403" in error_msg or "gated" in error_msg.lower() or "restricted" in error_msg.lower():
                    raise RuntimeError(
                        "SAM3 model access denied. Please:\n"
                        "1. Request access at huggingface.co/facebook/sam3\n"
                        "2. Add your HF token via Install SAM3 button\n"
                        "3. Restart the app"
                    )
                raise RuntimeError(f"Failed to load SAM3 model: {e}")

        # Load image
        if status_callback:
            status_callback("Processing with SAM3...")
        print(f"[SAM3] Loading image: {input_path}")
        image = Image.open(input_path).convert("RGBA")
        print(f"[SAM3] Image size: {image.size}")

        # Set image in processor
        print("[SAM3] Setting image in processor...")
        inference_state = self._processor.set_image(image.convert("RGB"))
        print(f"[SAM3] Inference state type: {type(inference_state)}")

        # Get text prompt
        prompt = options.get("prompt", "").strip()
        if not prompt:
            raise ValueError("SAM3 requires a text prompt")

        if status_callback:
            status_callback(f"Segmenting: {prompt}...")
        print(f"[SAM3] Running with prompt: '{prompt}'")

        # Run text-based segmentation
        output = self._processor.set_text_prompt(state=inference_state, prompt=prompt)
        print(f"[SAM3] Output keys: {output.keys() if isinstance(output, dict) else type(output)}")

        masks = output.get("masks", []) if isinstance(output, dict) else []
        scores = output.get("scores", []) if isinstance(output, dict) else []
        print(f"[SAM3] Found {len(masks)} masks, {len(scores)} scores")

        if len(masks) == 0:
            raise RuntimeError(f"No objects found matching '{prompt}'")

        # Use the best scoring mask
        best_idx = 0
        if len(scores) > 0:
            # Convert scores to CPU/numpy if it's a tensor
            if hasattr(scores, 'cpu'):
                scores_np = scores.cpu().numpy()
            elif hasattr(scores, 'numpy'):
                scores_np = scores.numpy()
            else:
                scores_np = np.array(scores)
            best_idx = int(np.argmax(scores_np))
            print(f"[SAM3] Best mask index: {best_idx}, score: {scores_np[best_idx]:.4f}")

        mask = masks[best_idx]

        # Convert mask to numpy if needed (move from GPU to CPU first)
        if hasattr(mask, 'cpu'):
            mask = mask.cpu().numpy()
        elif hasattr(mask, 'numpy'):
            mask = mask.numpy()

        # Ensure mask is 2D
        if len(mask.shape) > 2:
            mask = mask.squeeze()

        # Normalize mask to 0-255
        mask = (mask > 0.5).astype(np.uint8) * 255

        # Resize mask to match image if needed
        if mask.shape[:2] != (image.height, image.width):
            mask_img = Image.fromarray(mask)
            mask_img = mask_img.resize((image.width, image.height), Image.Resampling.LANCZOS)
            mask = np.array(mask_img)

        # Apply mask
        keep_subject = options.get("keep_subject", True)

        if not keep_subject:
            # Invert mask to remove the matched object instead
            mask = 255 - mask

        # Convert original to numpy for processing
        img_array = np.array(image)

        # Apply mask as alpha channel
        img_array[:, :, 3] = mask

        result = Image.fromarray(img_array, "RGBA")

        return result

    def is_available(self) -> bool:
        """Check if SAM3 is installed."""
        return SAM3_AVAILABLE

    def get_name(self) -> str:
        return "SAM3"

    def get_import_error(self) -> Optional[str]:
        """Get the import error message if SAM3 is not available."""
        return SAM3_IMPORT_ERROR

    def clear_model(self) -> None:
        """Clear the cached model (e.g., after token change)."""
        self._model = None
        self._processor = None


def is_sam3_available() -> bool:
    """Check if SAM3 is available."""
    return SAM3_AVAILABLE


def get_sam3_import_error() -> Optional[str]:
    """Get the SAM3 import error message."""
    return SAM3_IMPORT_ERROR
