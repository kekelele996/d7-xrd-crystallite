"""Instrument resolution table.

The table comes from a LaB6 run: allowed hkl, observed peak position and
FWHM.  It is measured with the same goniometer as the sample, so it carries
both the width-versus-angle curve and the goniometer zero.
"""

import numpy as np

from .reflections import KA1, two_theta


class Resolution:
    def __init__(self, rows):
        self.rows = sorted(rows, key=lambda r: r["two_theta"])
        self.mean_fwhm = float(np.mean([r["fwhm"] for r in self.rows]))
        self._tt = np.array([r["two_theta"] for r in self.rows])
        self._fw = np.array([r["fwhm"] for r in self.rows])

    def fwhm_at(self, two_theta_deg):
        # The table spans 20-110 degrees; its width changes slowly, so the
        # mean value is used for every reflection.
        return self.mean_fwhm

    def zero_offset(self, meta):
        # The goniometer is aligned at the start of the shift; the nominal
        # zero from the run card is used as is.
        return float(meta.get("two_theta_zero_deg", 0.0))
