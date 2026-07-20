"""Seed geopack's IGRF coefficients from a vendored local copy.

geopack.geopack unconditionally tries to download IGRF coefficient files from
NOAA over plain HTTP the first time it's imported, and raises an unhandled
ValueError if that fetch fails and no local copy exists yet (e.g. on a host
with no general internet egress). Call ensure_igrf_coeffs() before importing
`geopack.geopack` to avoid that network dependency entirely.
"""

from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

VENDORED_COEFFS_DIR = Path(__file__).resolve().parent / "igrf_coeffs"


def ensure_igrf_coeffs() -> None:
    spec = importlib.util.find_spec("geopack")
    if spec is None or not spec.submodule_search_locations:
        return

    package_dir = Path(next(iter(spec.submodule_search_locations)))
    igrf_dir = package_dir / "igrf_coeffs"
    igrf_dir.mkdir(parents=True, exist_ok=True)

    if any(igrf_dir.glob("igrf*coeffs.txt")):
        return

    for coeff_file in VENDORED_COEFFS_DIR.glob("igrf*coeffs.txt"):
        shutil.copy(coeff_file, igrf_dir / coeff_file.name)
