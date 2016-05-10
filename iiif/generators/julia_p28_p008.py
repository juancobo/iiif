"""Image generator for Julie set c = 0.28 + 0.008i.

Ref: <http://www.karlsims.com/julia.html>
"""

import cmath
from iiif.generators.mandlebrot_100k import PixelGen as PixelGenBase


class PixelGen(PixelGenBase):
    """Pixel generation class."""

    def set_c(self, z):
        """Set iteration constant for Julia set."""
        self.c = complex(0.28, 0.008)
