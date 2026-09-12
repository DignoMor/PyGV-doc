import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((REPO_ROOT / "code-ref.json").read_text(encoding="utf-8"))


def test_manifest_commit_is_full_sha():
    assert re.fullmatch(r"[0-9a-f]{40}", MANIFEST["commit"])


def test_manifest_declares_a_known_channel():
    assert MANIFEST["channel"] in {"stable", "development"}
    assert MANIFEST["branch"] in {"main", "dev"}


def test_channel_and_branch_are_consistent():
    expected = {"stable": "main", "development": "dev"}
    assert expected[MANIFEST["channel"]] == MANIFEST["branch"]


@pytest.mark.parametrize(
    "page", ["index.md", "overview.md", "installation.md", "provenance.md"]
)
def test_authored_page_exists(page):
    assert (REPO_ROOT / "docs" / page).is_file()


def test_quickstart_runs(tmp_path):
    script = REPO_ROOT / "docs" / "_examples" / "quickstart.py"
    output = tmp_path / "quickstart.png"
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"
    env["PYGV_QUICKSTART_OUT"] = str(output)
    subprocess.run([sys.executable, str(script)], check=True, cwd=tmp_path, env=env)
    assert output.is_file() and output.stat().st_size > 0


def test_built_site_reports_both_revisions():
    build = os.environ.get("PYGV_DOC_BUILD")
    if not build:
        pytest.skip("set PYGV_DOC_BUILD to a built HTML directory")
    index = (Path(build) / "index.html").read_text(encoding="utf-8")
    provenance = (Path(build) / "provenance.html").read_text(encoding="utf-8")
    assert MANIFEST["commit"][:7] in index
    assert "Build provenance" in provenance
