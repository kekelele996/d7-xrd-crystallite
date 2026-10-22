#!/usr/bin/env python3
"""Check the recheck entry point on three hidden runs.

Each check is one reduction step: Kalpha doublet width, instrument width
versus angle, goniometer zero.  The expected values are the forward-model
parameters from refkit/xrdcase.py, not the output of the reference solution.
"""

import json
import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from refkit.xrdcase import CASES, write_case  # noqa: E402
from score import record  # noqa: E402

APP = Path("/app")
PYTHON = "/usr/local/bin/python3"
CANDIDATE_USER = os.environ.get("HARBOR_CANDIDATE_USER", "runner")
CANDIDATE_ENV = {
    "PATH": "/usr/local/bin:/usr/bin:/bin",
    "HOME": f"/home/{CANDIDATE_USER}",
    "LANG": "C.UTF-8",
    "TZ": "UTC",
}
CALL_TIMEOUT_SEC = 20


def run_candidate(args, timeout=CALL_TIMEOUT_SEC):
    as_root = os.getuid() == 0
    proc = subprocess.Popen(
        [PYTHON, *[str(a) for a in args]],
        cwd=str(APP),
        env=CANDIDATE_ENV,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
        user=CANDIDATE_USER if as_root else None,
        group=CANDIDATE_USER if as_root else None,
        extra_groups=[] if as_root else None,
    )
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        out, err = proc.communicate()
        raise RuntimeError(f"timeout after {timeout}s")
    return subprocess.CompletedProcess(proc.args, proc.returncode, out, err)


def run_case(case_id):
    tmp = Path(tempfile.mkdtemp(prefix="in-"))
    tmp.chmod(0o755)
    truth = write_case(tmp, CASES[case_id])
    proc = run_candidate([APP / "xrd.py", tmp])
    if proc.returncode != 0:
        raise RuntimeError(f"exit={proc.returncode}, stderr={proc.stderr[:500]}")
    got = json.loads(proc.stdout)
    return truth, got


def relative_error(got, want):
    return abs(float(got) - float(want)) / abs(float(want))


def check_difficulty_1():
    """Coarse powder: the reported peak width must be the Kalpha1 component."""
    truth, got = run_case("difficulty_1")
    size_err = relative_error(got["size_nm"], truth["size_nm"])
    strain_err = abs(float(got["strain_pct"]) - float(truth["strain_pct"]))
    ok = size_err <= 0.12 and strain_err <= 0.05
    return ok, (f"size got={got['size_nm']:.3f} want={truth['size_nm']:.3f} "
                f"rel={size_err:.4f}; strain got={got['strain_pct']:.4f} "
                f"want={truth['strain_pct']:.4f} abs={strain_err:.4f}")


def check_difficulty_2():
    """Fine powder: the instrument width must follow the angle, not its mean."""
    truth, got = run_case("difficulty_2")
    size_err = relative_error(got["size_nm"], truth["size_nm"])
    ok = size_err <= 0.12
    return ok, (f"size got={got['size_nm']:.3f} want={truth['size_nm']:.3f} "
                f"rel={size_err:.4f}")


def check_difficulty_3():
    """Annealed powder: the standard table supplies the goniometer zero."""
    truth, got = run_case("difficulty_3")
    a_err = relative_error(got["lattice_a_angstrom"], truth["lattice_a_angstrom"])
    ok = a_err <= 2e-4
    return ok, (f"a got={got['lattice_a_angstrom']:.6f} "
                f"want={truth['lattice_a_angstrom']:.6f} rel={a_err:.6f}")


CHECKS = [
    ("difficulty_1", check_difficulty_1),
    ("difficulty_2", check_difficulty_2),
    ("difficulty_3", check_difficulty_3),
]


def main():
    for check_id, fn in CHECKS:
        try:
            ok, detail = fn()
        except Exception as exc:
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        record(check_id, ok, detail)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
