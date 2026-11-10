"""Approximate "natural" and "white balanced" color for MastCam images.

Raw MastCam images are not linear: on the rover, the 11-bit pixel values are
"companded" down to 8 bits with a square-root-like lookup table, after the
bias level has been subtracted. Color adjustments are multiplicative, so they
have to be applied to the linear values:

1. Decompand the 8-bit values back to linear 11-bit DN using "Lookup Table 0"
   from Bell et al. (2017), Appendix B.
2. Multiply each channel by a published coefficient:
   - natural: (1.2, 1, 1.0), approximately what a person standing on Mars
     would see. This is based on the MastCam color correction factors
     (1.2, 1, 1.26) from Bell et al. (2017) section 5.2.8, Eq. 13, and Malin
     et al. (2017) section 9.5, which correct for the camera's spectral
     response but keep the color of the Martian illumination. The published
     blue factor gives a pink cast, and does not match NASA's natural color
     example (PIA16800), where blue/green relative to raw measures about 0.96
     to 1.03, so blue is left unscaled. Red matches the published value.
   - white balanced: the multipliers (1, 1.16, 1.86) that Malin et al. (2017)
     section 9.5 give for "essentially white balanced color images". These
     also remove the reddish tint of the Martian sky light, estimating how the
     terrain would look under Earth-like lighting.
3. Compand back to 8 bits with Lookup Table 0, as is done for the PDS
   color-corrected products.

The coefficients are normalized so that green is 1. Exposure time is not known
from the JPEGs, so the overall brightness is arbitrary anyway, and this keeps
the brightness of the raw image and avoids clipping highlights.

References:
  Bell, J. F., III, et al. (2017), The Mars Science Laboratory Curiosity rover
  Mastcam instruments: Preflight and in-flight calibration, validation, and
  data archiving, Earth Space Sci., 4, 396-452, doi:10.1002/2016EA000219.

  Malin, M. C., et al. (2017), The Mars Science Laboratory (MSL) Mast cameras
  and Descent imager: Investigation and instrument descriptions, Earth Space
  Sci., 4, 506-539, doi:10.1002/2016EA000252.
"""

import numpy as np

COLOR_MODES = ("raw", "natural", "white-balanced")

# Bell et al. (2017) Appendix B: MastCam standard decompanding "Lookup Table 0"
# mapping 8-bit companded DN (the index) to 11-bit linear DN.
LUT0 = np.array(
    [
        0, 2, 3, 3, 4, 5, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15,
        16, 18, 19, 20, 22, 24, 25, 27, 29, 31, 33, 35, 37, 39, 41, 43,
        46, 48, 50, 53, 55, 58, 61, 63, 66, 69, 72, 75, 78, 81, 84, 87,
        90, 94, 97, 100, 104, 107, 111, 115, 118, 122, 126, 130, 134, 138, 142, 146,
        150, 154, 159, 163, 168, 172, 177, 181, 186, 191, 196, 201, 206, 211, 216, 221,
        226, 231, 236, 241, 247, 252, 258, 263, 269, 274, 280, 286, 292, 298, 304, 310,
        316, 322, 328, 334, 341, 347, 354, 360, 367, 373, 380, 387, 394, 401, 408, 415,
        422, 429, 436, 443, 450, 458, 465, 472, 480, 487, 495, 503, 510, 518, 526, 534,
        542, 550, 558, 566, 575, 583, 591, 600, 608, 617, 626, 634, 643, 652, 661, 670,
        679, 688, 697, 706, 715, 724, 733, 743, 752, 761, 771, 781, 790, 800, 810, 819,
        829, 839, 849, 859, 869, 880, 890, 900, 911, 921, 932, 942, 953, 964, 974, 985,
        996, 1007, 1018, 1029, 1040, 1051, 1062, 1074, 1085, 1096, 1108, 1119, 1131, 1142, 1154, 1166,
        1177, 1189, 1201, 1213, 1225, 1237, 1249, 1262, 1274, 1286, 1299, 1311, 1324, 1336, 1349, 1362,
        1374, 1387, 1400, 1413, 1426, 1439, 1452, 1465, 1479, 1492, 1505, 1519, 1532, 1545, 1559, 1573,
        1586, 1600, 1614, 1628, 1642, 1656, 1670, 1684, 1698, 1712, 1727, 1741, 1755, 1770, 1784, 1799,
        1814, 1828, 1843, 1858, 1873, 1888, 1903, 1918, 1933, 1948, 1963, 1979, 1994, 2009, 2025, 2033,
    ],
    dtype=np.float64,
)

# Per-channel (R, G, B) multipliers for linear DN.
COEFFICIENTS = {
    # Published blue factor is 1.26; see the module docstring.
    "natural": np.array([1.20, 1.00, 1.00]),
    "white-balanced": np.array([1.00, 1.16, 1.86]),
}


def decompand(companded: np.ndarray) -> np.ndarray:
    """Convert 8-bit companded DN to linear 11-bit DN using LUT 0."""
    return LUT0[companded.astype(np.intp)]


def compand(linear: np.ndarray) -> np.ndarray:
    """Convert linear 11-bit DN to (fractional) 8-bit companded DN using LUT 0."""
    return np.interp(linear, LUT0, np.arange(LUT0.size, dtype=np.float64))


def color_correct(linear_rgb: np.ndarray, mode: str) -> np.ndarray:
    """Scale linear RGB DN for ``mode``, normalized to green and clipped to 11 bits."""
    if mode not in COEFFICIENTS:
        raise ValueError(f"unknown color mode {mode!r}, expected one of {COLOR_MODES}")
    gains = COEFFICIENTS[mode] / COEFFICIENTS[mode][1]
    return np.clip(linear_rgb * gains, 0.0, LUT0[-1])
