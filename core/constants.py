"""
Constants and configuration values for the application.
"""

# Available rembg models with descriptions
REMBG_MODELS = {
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

# SAM3 is a special mode, not in the regular dropdown
SAM3_MODEL_INFO = "SAM3 - Text-based segmentation (270K+ concepts)"

# Output suffix options
SUFFIX_OPTIONS = [
    "_nobg",
    "_alpha",
    "_masked",
    "_transparent",
    "_cutout",
]

# Background color options: key -> (display_name, rgb_tuple or None for transparent)
BACKGROUND_OPTIONS = {
    "transparent": ("Transparent", None),
    "white": ("White", (255, 255, 255)),
    "black": ("Black", (0, 0, 0)),
}

# Supported image formats
VALID_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.tif'}

# Default configuration values
DEFAULT_CONFIG = {
    "model": "birefnet-general",
    "suffix": "_nobg",
    "background": "transparent",
    "alpha_matting": False,
    "alpha_matting_fg_threshold": 240,
    "alpha_matting_bg_threshold": 10,
    "alpha_matting_erode_size": 10,
    "output_format": "png",
    "auto_process": True,
    "use_sam3": False,
    "sam3_prompt": "",
    "sam3_keep_subject": True,
    "hf_token": "",
    "auto_crop": False,
    "auto_crop_margin": 10,
    "sticker_mode": False,
    "sticker_color": "#ffffff",
    "sticker_width": 5,
}

# Window dimensions
WINDOW_WIDTH = 580
WINDOW_HEIGHT = 880
MIN_WINDOW_WIDTH = 520
MIN_WINDOW_HEIGHT = 820

# Preview dimensions
PREVIEW_MAX_WIDTH = 250
PREVIEW_MAX_HEIGHT = 180
