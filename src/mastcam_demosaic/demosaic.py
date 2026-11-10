"""Bilinear de-mosaicing of Bayer-pattern images.

MastCam's sensor is covered by a Bayer filter: one row goes red, green, red,
green, ... and the next goes green, blue, green, blue, ... (an "RGGB" pattern).
Each pixel in a raw image therefore records only one color. To recover a full
color image, each color's known pixels are interpolated into the positions
where the other two colors were recorded.
"""

from pathlib import Path

import numpy as np
from PIL import Image

# Bayer layouts, named by the colors of the top-left 2x2 block read row by row.
PATTERNS = ("RGGB", "BGGR", "GRBG", "GBRG")

# Bilinear interpolation weights: direct neighbours count twice as much as
# diagonal ones, and the pixel itself counts the most.
_KERNEL = np.array([[1, 2, 1], [2, 4, 2], [1, 2, 1]], dtype=np.float64)


def _convolve3x3(data: np.ndarray) -> np.ndarray:
    """Convolve a 2D array with the 3x3 interpolation kernel (zero padded)."""
    padded = np.pad(data, 1)
    height, width = data.shape
    out = np.zeros_like(data)
    for dy in range(3):
        for dx in range(3):
            out += _KERNEL[dy, dx] * padded[dy : dy + height, dx : dx + width]
    return out


def _channel_masks(shape: tuple, pattern: str) -> dict:
    """Return a boolean mask per color marking where that color was sampled."""
    pattern = pattern.upper()
    if pattern not in PATTERNS:
        raise ValueError(f"unknown Bayer pattern {pattern!r}, expected one of {PATTERNS}")
    masks = {color: np.zeros(shape, dtype=bool) for color in "RGB"}
    for index, color in enumerate(pattern):
        y, x = divmod(index, 2)
        masks[color][y::2, x::2] = True
    return masks


def demosaic(raw: np.ndarray, pattern: str = "RGGB") -> np.ndarray:
    """De-mosaic a 2D Bayer-pattern array into an RGB array.

    For each color, the recorded pixels are kept as-is and the missing pixels
    are filled with a weighted average of the neighbouring pixels of that
    color (normalized convolution, which also handles the image edges).

    Returns a float64 array of shape (height, width, 3) in the input's range.
    """
    if raw.ndim != 2:
        raise ValueError("expected a single-channel (grayscale) Bayer image")
    raw = raw.astype(np.float64)
    masks = _channel_masks(raw.shape, pattern)

    channels = []
    for color in "RGB":
        mask = masks[color]
        weights = _convolve3x3(mask.astype(np.float64))
        interpolated = _convolve3x3(np.where(mask, raw, 0.0)) / weights
        channels.append(np.where(mask, raw, interpolated))
    return np.stack(channels, axis=-1)


def demosaic_file(src: Path, dst: Path, pattern: str = "RGGB", quality: int = 95) -> None:
    """Read a raw Bayer image from ``src`` and save the color result to ``dst``."""
    with Image.open(src) as img:
        if img.mode.startswith("I;16"):
            raw, scale = np.asarray(img), 257.0
        else:
            raw, scale = np.asarray(img.convert("L")), 1.0

    # Pillow cannot write 16-bit RGB, so 16-bit input is scaled down to 8 bits.
    rgb = demosaic(raw, pattern) / scale
    out = Image.fromarray(np.clip(np.rint(rgb), 0, 255).astype(np.uint8), "RGB")

    save_kwargs = {}
    if dst.suffix.lower() in (".jpg", ".jpeg"):
        save_kwargs = {"quality": quality, "subsampling": 0}
    out.save(dst, **save_kwargs)
