"""
Image processing utilities - crop, sticker effects, preview generation.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from typing import Tuple, Optional


def auto_crop_image(image: Image.Image, margin: int = 10) -> Image.Image:
    """
    Crop image to the bounding box of non-transparent pixels with margin.

    Args:
        image: PIL Image with transparency
        margin: Pixels of padding around the object

    Returns:
        Cropped PIL Image
    """
    # Convert to RGBA if needed
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # Get alpha channel
    alpha = np.array(image)[:, :, 3]

    # Find non-transparent pixels
    rows = np.any(alpha > 0, axis=1)
    cols = np.any(alpha > 0, axis=0)

    if not np.any(rows) or not np.any(cols):
        # No visible pixels, return original
        return image

    # Get bounding box
    row_indices = np.where(rows)[0]
    col_indices = np.where(cols)[0]
    top, bottom = row_indices[0], row_indices[-1]
    left, right = col_indices[0], col_indices[-1]

    # Add margin
    top = max(0, top - margin)
    left = max(0, left - margin)
    bottom = min(image.height - 1, bottom + margin)
    right = min(image.width - 1, right + margin)

    # Crop
    cropped = image.crop((left, top, right + 1, bottom + 1))

    return cropped


def add_sticker_outline(
    image: Image.Image,
    outline_width: int = 5,
    outline_color: Tuple[int, int, int] = (255, 255, 255)
) -> Image.Image:
    """
    Add a colored outline/stroke around the subject in an RGBA image.
    Creates a "sticker" effect with an opaque outline and transparent background.

    Args:
        image: PIL Image with transparency (RGBA)
        outline_width: Width of the outline in pixels
        outline_color: RGB tuple for the outline color

    Returns:
        PIL Image with sticker outline effect
    """
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # Get the alpha channel
    alpha = image.split()[3]

    # Create a dilated (expanded) version of the alpha mask
    # This creates the outline area
    dilated_alpha = alpha.copy()

    # Apply dilation by using maximum filter multiple times
    # Each iteration expands the mask by ~1 pixel
    for _ in range(outline_width):
        dilated_alpha = dilated_alpha.filter(ImageFilter.MaxFilter(3))

    # Create the outline mask (dilated - original = outline area)
    outline_mask = np.array(dilated_alpha).astype(np.int16) - np.array(alpha).astype(np.int16)
    outline_mask = np.clip(outline_mask, 0, 255).astype(np.uint8)
    outline_mask_img = Image.fromarray(outline_mask)

    # Create the final image with enough space for the outline
    # We need to expand the canvas by outline_width on each side
    new_width = image.width + (outline_width * 2)
    new_height = image.height + (outline_width * 2)

    # Create the outline layer (solid color where outline_mask is non-zero)
    outline_layer = Image.new("RGBA", (new_width, new_height), (0, 0, 0, 0))
    outline_solid = Image.new("RGBA", image.size, outline_color + (255,))

    # Expand masks to new canvas size
    expanded_dilated_alpha = Image.new("L", (new_width, new_height), 0)
    expanded_dilated_alpha.paste(dilated_alpha, (outline_width, outline_width))

    # Create the outline on expanded canvas
    expanded_outline_solid = Image.new("RGBA", (new_width, new_height), outline_color + (255,))
    outline_layer = Image.composite(
        expanded_outline_solid,
        outline_layer,
        expanded_dilated_alpha
    )

    # Paste the original image centered
    result = outline_layer.copy()
    result.paste(image, (outline_width, outline_width), image)

    return result


def create_checkerboard_preview(
    image: Image.Image,
    max_size: Tuple[int, int] = (250, 180),
    checker_size: int = 10
) -> Image.Image:
    """
    Create a preview image with checkerboard background for transparent images.

    Args:
        image: PIL Image to preview
        max_size: Maximum (width, height) for the preview
        checker_size: Size of checkerboard squares

    Returns:
        RGB PIL Image with checkerboard behind transparent areas
    """
    # Create thumbnail
    preview = image.copy()
    preview.thumbnail(max_size, Image.Resampling.LANCZOS)

    # For transparent images, add a checkerboard background
    if preview.mode == "RGBA":
        checker = Image.new("RGB", preview.size, (200, 200, 200))
        for y in range(0, preview.height, checker_size):
            for x in range(0, preview.width, checker_size):
                if (x // checker_size + y // checker_size) % 2:
                    for py in range(y, min(y + checker_size, preview.height)):
                        for px in range(x, min(x + checker_size, preview.width)):
                            checker.putpixel((px, py), (255, 255, 255))
        checker.paste(preview, mask=preview.split()[3])
        return checker

    return preview


def apply_background_color(
    image: Image.Image,
    bg_color: Optional[Tuple[int, int, int]]
) -> Image.Image:
    """
    Apply a solid background color to an RGBA image, or keep transparent.

    Args:
        image: PIL Image with transparency
        bg_color: RGB tuple for background, or None for transparent

    Returns:
        PIL Image (RGB if bg_color, RGBA if None)
    """
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    if bg_color is not None:
        # Composite onto solid background
        background = Image.new("RGBA", image.size, bg_color + (255,))
        composite = Image.alpha_composite(background, image)
        return composite.convert("RGB")
    else:
        return image
