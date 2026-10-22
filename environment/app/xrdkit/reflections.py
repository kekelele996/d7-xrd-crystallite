"""Cubic fluorite-type reflection table and Bragg helpers.

The phase is known from the batch card; only its lattice parameter is unknown.
A0 is the nominal lattice parameter used to label the observed peaks.  It is
not the answer: the observed positions are refined independently.
"""

import math

KA1 = 1.540598
KA2 = 1.544426
KA2_RATIO = 0.5
A0 = 5.411


def d_spacing(a, hkl):
    h, k, l = hkl
    return a / math.sqrt(h * h + k * k + l * l)


def two_theta(wavelength, a, hkl):
    d = d_spacing(a, hkl)
    return 2.0 * math.degrees(math.asin(wavelength / (2.0 * d)))


def table(a=A0, lo=20.5, hi=109.5):
    """Unique allowed reflections of a face-centred cubic lattice, by 2theta."""
    seen = {}
    for h in range(0, 9):
        for k in range(0, 9):
            for l in range(0, 9):
                if h == k == l == 0:
                    continue
                if not (h % 2 == k % 2 == l % 2):
                    continue
                n = h * h + k * k + l * l
                d = a / math.sqrt(n)
                if KA1 / (2.0 * d) >= 1.0:
                    continue
                tt = two_theta(KA1, a, (h, k, l))
                if not (lo < tt < hi):
                    continue
                key = round(tt, 3)
                if key not in seen:
                    seen[key] = {"hkl": (h, k, l), "n": n, "two_theta": tt}
    return sorted(seen.values(), key=lambda r: r["two_theta"])
