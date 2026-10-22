"""Size/strain and lattice-parameter reduction."""

import math

import numpy as np

from .peaks import reported_width
from .reflections import A0, KA1, table


def beta_of_fwhm(fwhm_deg):
    """Integral breadth of a Lorentzian profile, in radians."""
    return math.pi / 2.0 * math.radians(fwhm_deg)


def _match(peaks, zero):
    """Label each fitted peak with the reflection index n."""
    refs = table(A0)
    labelled = []
    for peak in peaks:
        best = min(refs, key=lambda r: abs(r["two_theta"] + zero - peak["two_theta"]))
        if abs(best["two_theta"] + zero - peak["two_theta"]) < 0.6:
            labelled.append((best["n"], peak))
    # one peak per reflection, keep the closest fit
    seen = {}
    for n, peak in labelled:
        ref = next(r for r in refs if r["n"] == n)
        err = abs(ref["two_theta"] + zero - peak["two_theta"])
        if n not in seen or err < seen[n][0]:
            seen[n] = (err, peak)
    return [(n, peak) for n, (err, peak) in sorted(seen.items())]


def size_strain(peaks, resolution, meta):
    """Williamson-Hall line fit on integral breadths."""
    k = float(meta.get("scherrer_k", 0.9))
    xs, ys = [], []
    for peak in peaks:
        fw = reported_width(peak["fwhm_component"], peak["fwhm_envelope"])
        beta = beta_of_fwhm(fw) - beta_of_fwhm(resolution.fwhm_at(peak["two_theta"]))
        if beta <= 1e-6:
            continue
        theta = math.radians(peak["two_theta"] / 2.0)
        xs.append(math.sin(theta))
        ys.append(beta * math.cos(theta))
    if len(xs) < 5:
        raise ValueError("not enough usable peaks")
    x = np.array(xs)
    y = np.array(ys)
    slope, intercept = np.linalg.lstsq(np.vstack([x, np.ones_like(x)]).T, y, rcond=None)[0]

    # One bad profile can tilt the whole line; drop points far from the fit.
    residual = y - (slope * x + intercept)
    mad = np.median(np.abs(residual - np.median(residual)))
    keep = np.abs(residual) < max(3.0 * mad, 2e-4)
    if keep.sum() >= 5:
        x, y = x[keep], y[keep]
        slope, intercept = np.linalg.lstsq(np.vstack([x, np.ones_like(x)]).T, y, rcond=None)[0]
    if intercept <= 0:
        raise ValueError("non-positive Williamson-Hall intercept")
    return k * KA1 * 1e-10 / intercept * 1e9, slope / 4.0 * 100.0


def lattice_constant(peaks, resolution, meta):
    """Cubic lattice parameter from the Kalpha1 peak positions."""
    zero = resolution.zero_offset(meta)
    labelled = _match(peaks, zero)
    if len(labelled) < 5:
        raise ValueError("not enough indexed peaks")
    values = []
    for n, peak in labelled:
        xc = peak["two_theta"] - zero
        d = KA1 / (2.0 * math.sin(math.radians(xc / 2.0)))
        values.append(d * math.sqrt(n))
    return float(np.median(values))


def reduce_run(peaks, resolution, meta):
    size, strain = size_strain(peaks, resolution, meta)
    a = lattice_constant(peaks, resolution, meta)
    return {"size_nm": size, "strain_pct": strain, "lattice_a_angstrom": a}
