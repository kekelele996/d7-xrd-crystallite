#!/usr/bin/env python3
"""Replace the candidate lattice reduction with a zero + displacement fit."""

from pathlib import Path

OLD = '''def lattice_constant(peaks, resolution, meta):
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
    return float(np.median(values))'''

NEW = '''def lattice_constant(peaks, resolution, meta):
    """Cubic lattice parameter with the specimen-displacement term."""
    from scipy.optimize import least_squares
    zero = resolution.zero_offset(meta)
    labelled = _match(peaks, zero)
    if len(labelled) < 5:
        raise ValueError("not enough indexed peaks")
    guess = []
    for n, peak in labelled:
        xc = peak["two_theta"] - zero
        d = KA1 / (2.0 * math.sin(math.radians(xc / 2.0)))
        guess.append(d * math.sqrt(n))
    a0 = float(np.median(guess))

    def residual(p):
        a, disp = p
        out = []
        for n, peak in labelled:
            theta = math.radians(peak["two_theta"] / 2.0)
            calc = 2.0 * math.degrees(math.asin(min(0.999999, KA1 * math.sqrt(n) / (2.0 * a))))
            calc += zero + math.degrees(-2.0 * disp * math.cos(theta) / 240.0)
            out.append(peak["two_theta"] - calc)
        return out

    fit = least_squares(residual, [a0, 0.0], bounds=([5.2, -2.0], [5.6, 2.0]))
    return float(fit.x[0])'''

path = Path("/app/xrdkit/analysis.py")
text = path.read_text()
if OLD not in text:
    raise SystemExit("difficulty_3 lattice anchor missing")
path.write_text(text.replace(OLD, NEW))
