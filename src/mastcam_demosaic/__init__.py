"""De-mosaic raw Bayer-pattern images from the Curiosity rover's MastCam."""

from .demosaic import PATTERNS, demosaic, demosaic_file

__all__ = ["PATTERNS", "demosaic", "demosaic_file"]
__version__ = "0.1.0"
