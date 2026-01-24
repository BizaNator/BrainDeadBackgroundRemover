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

import sys
import os
import io
import logging


class NullWriter(io.IOBase):
    """No-op writer for PyInstaller --windowed mode where stdout/stderr are None."""
    def write(self, *args, **kwargs):
        return 0
    def flush(self, *args, **kwargs):
        pass
    def isatty(self):
        return False
    def readable(self):
        return False
    def writable(self):
        return True
    def fileno(self):
        raise OSError("NullWriter does not use a file descriptor")


# Fix for PyInstaller --windowed mode: sys.stdout/stderr are None
# which causes crashes on any print() or logging write() call
if sys.stdout is None:
    sys.stdout = NullWriter()
if sys.stderr is None:
    sys.stderr = NullWriter()
if sys.__stdout__ is None:
    sys.__stdout__ = sys.stdout
if sys.__stderr__ is None:
    sys.__stderr__ = sys.stderr

# Suppress onnxruntime verbose logging
os.environ["ONNXRUNTIME_LOG_SEVERITY_LEVEL"] = "3"

# Prevent logging handlers from writing to None streams in windowed mode
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle - suppress all logging
    logging.disable(logging.CRITICAL)
    logging.root.handlers = [logging.NullHandler()]

from ui.main_window import BackgroundRemoverApp


def main():
    app = BackgroundRemoverApp()
    app.run()


if __name__ == "__main__":
    main()
