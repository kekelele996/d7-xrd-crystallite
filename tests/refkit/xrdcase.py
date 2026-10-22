"""Generate a powder XRD recheck run with a known size, strain and lattice.

The generator is a forward model.  It is the source of the expected values in
the checks; the reference solution never feeds values back into it.
"""

import csv
import json
import math
from pathlib import Path

import numpy as np

KA1 = 1.540598
KA2 = 1.544426
KA2_RATIO = 0.5
A_STD = 4.156826
A0 = 5.411


def d_of(a, hkl):
    h, k, l = hkl
    return a / math.sqrt(h * h + k * k + l * l)


def tt_of(lam, d):
    return 2.0 * math.degrees(math.asin(lam / (2.0 * d)))


def reflections(a, lo=20.5, hi=109.5, centred=True):
    seen = {}
    for h in range(0, 9):
        for k in range(0, 9):
            for l in range(0, 9):
                if h == k == l == 0:
                    continue
                if centred and not (h % 2 == k % 2 == l % 2):
                    continue
                n = h * h + k * k + l * l
                d = a / math.sqrt(n)
                if KA1 / (2.0 * d) >= 1.0:
                    continue
                tt = tt_of(KA1, d)
                if not (lo < tt < hi):
                    continue
                key = round(tt, 3)
                if key not in seen:
                    seen[key] = (h, k, l, n, tt)
    return sorted(seen.values(), key=lambda r: r[4])


def caglioti(u, v, w, tt):
    t = math.tan(math.radians(tt / 2.0))
    return math.sqrt(max(1e-9, u * t * t + v * t + w))


def beta_of_fwhm(f):
    return math.pi / 2.0 * math.radians(f)


def fwhm_of_beta(b):
    return math.degrees(2.0 * b / math.pi)


def lorentz(x, x0, fwhm):
    g = fwhm / 2.0
    return g * g / ((x - x0) ** 2 + g * g)


def instrument_table(u, v, w, delta):
    rows = []
    for h, k, l, n, tt in reflections(A_STD, centred=False):
        x = tt + delta
        rows.append(((h, k, l), x, caglioti(u, v, w, x)))
    return rows


def write_case(path, spec):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(int(spec["seed"]))
    x = np.arange(20.0, 110.0 + 1e-9, float(spec.get("step", 0.005)))
    y = 45.0 + 0.3 * x + 100.0 * np.exp(-0.5 * ((x - 24.0) / 6.0) ** 2)
    a = float(spec["a"])
    size = float(spec["size_nm"])
    strain = float(spec["strain_pct"])
    u, v, w = spec["instrument"]
    delta = float(spec["delta"])
    counts = float(spec.get("counts", 100000))
    for h, k, l, n, tt in reflections(a):
        tt1 = tt + delta
        tt2 = tt_of(KA2, d_of(a, (h, k, l))) + delta
        theta = math.radians(tt1 / 2.0)
        beta = (0.9 * KA1 * 1e-10 / (size * 1e-9 * math.cos(theta))
                + 4.0 * (strain / 100.0) * math.tan(theta)
                + beta_of_fwhm(caglioti(u, v, w, tt1)))
        fwhm = fwhm_of_beta(beta)
        amp = counts * math.exp(-0.012 * n)
        y += amp * (lorentz(x, tt1, fwhm) + KA2_RATIO * lorentz(x, tt2, fwhm))
    y = rng.poisson(np.maximum(y, 0.1)).astype(int)

    with open(path / "sample.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["two_theta_deg", "counts"])
        for xx, yy in zip(x, y):
            writer.writerow([f"{xx:.3f}", int(yy)])

    with open(path / "instrument.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["h", "k", "l", "two_theta_deg", "fwhm_deg"])
        for (h, k, l), tt, fwhm in instrument_table(u, v, w, delta):
            writer.writerow([h, k, l, f"{tt:.4f}", f"{fwhm:.5f}"])

    meta = {
        "sample_id": spec["sample_id"],
        "phase": "cubic fluorite",
        "wavelength_ka1_angstrom": KA1,
        "wavelength_ka2_angstrom": KA2,
        "ka2_intensity_ratio": KA2_RATIO,
        "lattice_std_angstrom": A_STD,
        "two_theta_zero_deg": 0.0,
        "scherrer_k": 0.9,
        "two_theta_step_deg": float(spec.get("step", 0.005)),
    }
    (path / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
                                    encoding="utf-8")

    truth = {
        "sample_id": spec["sample_id"],
        "size_nm": size,
        "strain_pct": strain,
        "lattice_a_angstrom": a,
    }
    if spec.get("certificate"):
        cert = {"sample_id": spec["sample_id"], "size_nm": size,
                "lattice_a_angstrom": a}
        (path / "certificate.json").write_text(
            json.dumps(cert, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return truth


# Three hidden cases: each one is dominated by a different reduction step.
CASES = {
    "difficulty_1": {
        "sample_id": "R-9184",
        "a": 5.405,
        "size_nm": 120.0,
        "strain_pct": 0.05,
        "instrument": (0.0, 0.0, 0.0064),
        "delta": 0.0,
        "seed": 101,
    },
    "difficulty_2": {
        "sample_id": "R-2271",
        "a": 5.418,
        "size_nm": 8.0,
        "strain_pct": 0.10,
        "instrument": (0.050, 0.005, 0.010),
        "delta": 0.0,
        "seed": 202,
    },
    "difficulty_3": {
        "sample_id": "R-6640",
        "a": 5.397,
        "size_nm": 12.0,
        "strain_pct": 0.10,
        "instrument": (0.0, 0.0, 0.0064),
        "delta": 0.12,
        "seed": 303,
    },
}

PUBLIC = {
    "S-01": {
        "sample_id": "S-01", "a": 5.411, "size_nm": 5.0, "strain_pct": 0.08,
        "instrument": (0.0, 0.0, 0.0064), "delta": 0.0, "seed": 11, "certificate": True,
    },
    "S-02": {
        "sample_id": "S-02", "a": 5.402, "size_nm": 6.0, "strain_pct": 0.12,
        "instrument": (0.0, 0.0, 0.0064), "delta": 0.0, "seed": 12, "certificate": True,
    },
}


if __name__ == "__main__":
    import sys
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("cases")
    for name, spec in PUBLIC.items():
        truth = write_case(out / name, spec)
        print(name, truth)
