"""
BrainDead Background Remover
A lightweight, portable drag-and-drop background removal utility.
Uses rembg with BiRefNet and other models for high-quality results.
Optional SAM3 support for text-based segmentation.

This is the main entry point. The application has been refactored into modules:
- core/: Constants, configuration management
- processors/: Image processing backends (rembg, SAM3)
- ui/: User interface components
- utils/: GPU detection, image utilities
"""

from ui.main_window import BackgroundRemoverApp


def main():
    app = BackgroundRemoverApp()
    app.run()


if __name__ == "__main__":
    main()
