"""Peak search and profile fit.

Each observed peak is a Kalpha doublet: two Lorentzians with the same width,
the second one weaker and shifted to a slightly shorter wavelength.  The fit
returns both widths so the caller can decide which one describes the
crystallite broadening.
"""

import math

import numpy as np
from scipy.optimize import least_squares
from scipy.signal import find_peaks

from .reflections import KA1, KA2, KA2_RATIO


def lorentz(x, x0, fwhm):
    g = fwhm / 2.0
    return g * g / ((x - x0) ** 2 + g * g)


def ka2_position(x1):
    s = min(0.999999, KA2 / KA1 * math.sin(math.radians(x1 / 2.0)))
    return 2.0 * math.degrees(math.asin(s))


def envelope_fwhm(x1, fw):
    """Full width at half maximum of the summed Kalpha1+Kalpha2 envelope."""
    x2 = ka2_position(x1)
    xs = np.linspace(x1 - 5.0 * fw - 1.0, x1 + 5.0 * fw + 1.0, 4001)
    ys = lorentz(xs, x1, fw) + KA2_RATIO * lorentz(xs, x2, fw)
    half = ys.max() / 2.0
    idx = np.where(ys >= half)[0]
    if len(idx) < 2:
        return fw
    return float(xs[idx[-1]] - xs[idx[0]])


def reported_width(component_fwhm, envelope_width):
    """The width handed to the size/strain analysis."""
    return envelope_width


def find_centers(x, y):
    """Candidate peak centres, merged across the Kalpha doublet."""
    pk, _ = find_peaks(y, prominence=900, distance=12)
    groups = []
    for i in pk:
        if groups and x[i] - x[groups[-1][-1]] < 2.0:
            groups[-1].append(i)
        else:
            groups.append([i])
    centers = []
    for group in groups:
        j = max(group, key=lambda i: y[i])
        if y[j] > 1800:
            centers.append(float(x[j]))
    return centers


def fit_doublet(x, y, center, half):
    lo, hi = center - half, center + half
    mask = (x >= lo) & (x <= hi)
    xx, yy = x[mask], y[mask]
    if len(xx) < 8:
        return None

    def model(p):
        x1, fw, amp, b0, b1 = p
        x2 = ka2_position(x1)
        return (b0 + b1 * (xx - center)
                + amp * (lorentz(xx, x1, fw) + KA2_RATIO * lorentz(xx, x2, fw)))

    p0 = [center, 0.3, max(yy.max() - 60.0, 100.0), 60.0, 0.2]
    lb = [center - 0.7, 0.03, 0.0, -1e5, -100.0]
    ub = [center + 0.7, 4.0, 1e7, 1e5, 100.0]
    res = least_squares(lambda p: model(p) - yy, p0, bounds=(lb, ub), max_nfev=4000)
    x1, fw, amp, b0, b1 = res.x
    if fw < 0.03 or fw > 3.5 or amp < 300.0:
        return None
    rmse = float(np.sqrt(np.mean((model(res.x) - yy) ** 2)))
    return {
        "two_theta": float(x1),
        "fwhm_component": float(fw),
        "fwhm_envelope": envelope_fwhm(float(x1), float(fw)),
        "rmse": rmse,
        "amplitude": float(amp),
    }


def fit_all(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    centers = find_centers(x, y)
    peaks = []
    for i, center in enumerate(centers):
        left = center - centers[i - 1] if i > 0 else 9.0
        right = centers[i + 1] - center if i + 1 < len(centers) else 9.0
        half = min(2.2, 0.42 * min(left, right))
        peak = fit_doublet(x, y, center, half)
        if peak is not None:
            peaks.append(peak)
    peaks.sort(key=lambda p: p["two_theta"])
    return peaks
