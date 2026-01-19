# Third-Party Models and Licenses

BrainDead Background Remover uses third-party AI models for background removal. These models are **not** part of this repository and are **not** covered by the GPL-3.0 license that applies to this application's source code.

Each model is downloaded at runtime and remains under its original license. You must comply with each model's license terms when using this software.

## Auto Mode Models (via rembg)

These models are accessed through the [rembg](https://github.com/danielgatis/rembg) library.

| Model | Description | Original Source | License |
|-------|-------------|-----------------|---------|
| `birefnet-general` | Best quality, most accurate | [BiRefNet](https://github.com/ZhengPeng7/BiRefNet) | MIT |
| `birefnet-general-lite` | Faster, good quality | [BiRefNet](https://github.com/ZhengPeng7/BiRefNet) | MIT |
| `birefnet-portrait` | Optimized for faces | [BiRefNet](https://github.com/ZhengPeng7/BiRefNet) | MIT |
| `birefnet-dis` | Dichotomous segmentation | [BiRefNet](https://github.com/ZhengPeng7/BiRefNet) | MIT |
| `birefnet-hrsod` | High-res salient objects | [BiRefNet](https://github.com/ZhengPeng7/BiRefNet) | MIT |
| `birefnet-cod` | Concealed object detection | [BiRefNet](https://github.com/ZhengPeng7/BiRefNet) | MIT |
| `birefnet-massive` | Large dataset trained | [BiRefNet](https://github.com/ZhengPeng7/BiRefNet) | MIT |
| `u2net` | Classic model, balanced | [U-2-Net](https://github.com/xuebinqin/U-2-Net) | Apache 2.0 |
| `u2netp` | Lightweight, fast | [U-2-Net](https://github.com/xuebinqin/U-2-Net) | Apache 2.0 |
| `u2net_human_seg` | Human segmentation | [U-2-Net](https://github.com/xuebinqin/U-2-Net) | Apache 2.0 |
| `u2net_cloth_seg` | Clothing segmentation | [U-2-Net](https://github.com/xuebinqin/U-2-Net) | Apache 2.0 |
| `isnet-general-use` | Good all-around | [DIS](https://github.com/xuebinqin/DIS) | Apache 2.0 |
| `isnet-anime` | Anime/illustration | [DIS](https://github.com/xuebinqin/DIS) | Apache 2.0 |
| `sam` | Segment Anything Model | [SAM](https://github.com/facebookresearch/segment-anything) | Apache 2.0 |

### rembg Library

- **Repository**: https://github.com/danielgatis/rembg
- **License**: MIT
- **Note**: rembg is a wrapper library; individual model weights have their own licenses as listed above.

## SAM3 Mode (Optional GPU Mode)

SAM3 (Segment Anything Model 3) is a gated model from Meta that requires:
1. A Hugging Face account
2. Explicit approval from Meta to access the model
3. Agreement to Meta's license terms

| Component | Source | License |
|-----------|--------|---------|
| SAM3 Model | [facebook/sam3](https://huggingface.co/facebook/sam3) | Meta License (gated) |
| PyTorch | [pytorch.org](https://pytorch.org) | BSD-3-Clause |
| CLIP (BPE vocab) | [openai/CLIP](https://github.com/openai/CLIP) | MIT |

### SAM3 License Terms

SAM3 is released under Meta's custom license. Key points:
- You must request and receive access on Hugging Face before use
- Review the full license at: https://huggingface.co/facebook/sam3
- Commercial use may have restrictions - check the license carefully

## Other Dependencies

| Dependency | Purpose | License |
|------------|---------|---------|
| Pillow | Image processing | HPND |
| NumPy | Array operations | BSD-3-Clause |
| ONNX Runtime | Model inference | MIT |
| tkinterdnd2 | Drag and drop | MIT |
| huggingface_hub | Model downloads | Apache 2.0 |

## Model Storage

Models are downloaded on first use and cached locally:
- **rembg models**: `~/.u2net/` directory
- **SAM3 models**: Hugging Face cache (`~/.cache/huggingface/`)

## Disclaimer

This application is a GUI wrapper that facilitates the use of these third-party models. The application author does not claim ownership of or responsibility for the underlying AI models. Users are responsible for ensuring their use of each model complies with its respective license terms.

For commercial use, please review each model's license carefully, particularly SAM3's Meta license which may have specific restrictions.
