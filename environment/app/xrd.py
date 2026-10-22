"""Ceramic powder XRD recheck: crystallite size, microstrain, lattice parameter."""

import json
import sys

from xrdkit.analysis import reduce_run
from xrdkit.instrument import Resolution
from xrdkit.io import load_instrument, load_meta, load_sample
from xrdkit.peaks import fit_all


def main(argv):
    if len(argv) != 2:
        print("usage: python3 xrd.py <run_dir>", file=sys.stderr)
        return 2
    run_dir = argv[1]
    meta = load_meta(run_dir)
    x, y = load_sample(run_dir)
    rows = load_instrument(run_dir)
    peaks = fit_all(x, y)
    result = reduce_run(peaks, Resolution(rows), meta)
    print(json.dumps({
        "size_nm": round(result["size_nm"], 6),
        "strain_pct": round(result["strain_pct"], 6),
        "lattice_a_angstrom": round(result["lattice_a_angstrom"], 6),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
