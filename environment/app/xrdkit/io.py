"""Read one recheck run directory."""

import csv
import json
from pathlib import Path


def load_meta(run_dir):
    with open(Path(run_dir) / "meta.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_sample(run_dir):
    xs, ys = [], []
    with open(Path(run_dir) / "sample.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            xs.append(float(row["two_theta_deg"]))
            ys.append(float(row["counts"]))
    return xs, ys


def load_instrument(run_dir):
    rows = []
    with open(Path(run_dir) / "instrument.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "hkl": (int(row["h"]), int(row["k"]), int(row["l"])),
                "two_theta": float(row["two_theta_deg"]),
                "fwhm": float(row["fwhm_deg"]),
            })
    return rows
