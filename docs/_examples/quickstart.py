"""Runnable quickstart used by the documentation.

The documentation includes the code between the ``quickstart`` markers. The
test suite executes this module so the published snippet cannot drift from a
working program.
"""

import os
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from pygv.tracks import BedTrack
from pygv.viewer import GenomeViewer

BED_CONTENT = "chr1\t10\t30\tfeature_a\nchr1\t40\t70\tfeature_b\n"


def _write_bed(directory: Path) -> Path:
    bed_path = directory / "features.bed"
    bed_path.write_text(BED_CONTENT, encoding="utf-8")
    return bed_path


# --8<-- [start:quickstart]
with tempfile.TemporaryDirectory() as tmp:
    bed_path = Path(tmp) / "features.bed"
    bed_path.write_text("chr1\t10\t30\tfeature_a\nchr1\t40\t70\tfeature_b\n")

    gv = GenomeViewer()
    gv.add_track(BedTrack(str(bed_path), name="Example features"))
    gv.plot("chr1", 0, 100)
    gv.save(os.environ.get("PYGV_QUICKSTART_OUT", "pygv-quickstart.png"))
# --8<-- [end:quickstart]
