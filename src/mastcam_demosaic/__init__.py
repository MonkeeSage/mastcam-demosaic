"""De-mosaic raw Bayer-pattern images from the Curiosity rover's MastCam."""

from .color import COLOR_MODES
from .demosaic import PATTERNS, demosaic, demosaic_file

__all__ = ["COLOR_MODES", "PATTERNS", "demosaic", "demosaic_file"]
__version__ = "0.1.0"
