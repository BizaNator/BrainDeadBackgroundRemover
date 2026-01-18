# BrainDead Background Remover

A lightweight, portable drag-and-drop background removal utility using AI models.

## Features

- **Drag & Drop**: Just drop an image onto the window
- **Multiple AI Models**: BiRefNet, U2Net, ISNet, SAM
- **Alpha Matting**: Better edge quality with adjustable thresholds
- **Portable**: No installer needed, single executable
- **Auto-save**: Outputs to same folder as input with configurable suffix
- **Settings Persistence**: Remembers your preferences

## Supported Models

| Model | Description |
|-------|-------------|
| birefnet-general | Best quality, most accurate (recommended) |
| birefnet-general-lite | Faster, good quality |
| birefnet-portrait | Optimized for faces/portraits |
| birefnet-dis | Dichotomous segmentation |
| birefnet-hrsod | High-resolution salient objects |
| birefnet-cod | Concealed object detection |
| birefnet-massive | Large dataset trained |
| u2net | Classic model, balanced |
| u2netp | Lightweight, fast |
| u2net_human_seg | Human segmentation |
| isnet-general-use | Good all-around |
| isnet-anime | Anime/illustration optimized |
| sam | Segment Anything Model |

## Installation

### Option 1: Run from Source (Recommended for Development)

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run
python bg_remover.py
```

### Option 2: Build Portable Executable

```bash
# Install dependencies first
pip install -r requirements.txt
pip install pyinstaller

# Build (Windows)
build.bat

# Or manually:
pyinstaller --onefile --windowed --name BrainDeadBGRemover \
    --hidden-import rembg \
    --collect-all rembg \
    --collect-data tkinterdnd2 \
    bg_remover.py
```

## Usage

1. Launch the application
2. Drop an image onto the window (or click to browse)
3. Background is automatically removed
4. Output saved to same folder as input with suffix (e.g., `image_nobg.png`)

### Settings

- **Model**: Choose the AI model for removal
- **Output suffix**: Customize the output filename suffix
- **Alpha Matting**: Enable for better edge quality (slower)
  - FG Threshold: Pixels above this are foreground
  - BG Threshold: Pixels below this are background
  - Erode Size: Edge erosion amount

## Supported Formats

- Input: PNG, JPG, JPEG, WEBP, BMP, TIFF
- Output: PNG (with transparency)

## Notes

- First run downloads the selected AI model (~170MB for BiRefNet)
- Models are cached in `~/.u2net/`
- Settings saved in `bg_remover_config.json` next to executable

## Requirements

- Python 3.10+
- Windows/Linux/macOS

## License

MIT License
