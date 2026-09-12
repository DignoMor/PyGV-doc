import html
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((REPO_ROOT / "code-ref.json").read_text(encoding="utf-8"))

VIEWER_METHODS = [
    "add_track",
    "add_tracks",
    "remove_track",
    "add_group_autoscale",
    "add_group_autoscale_by_name",
    "add_group_label",
    "add_group_label_by_name",
    "reset_group_autoscale",
    "set_highlight_regions",
    "set_global_highlight_region",
    "set_global_vertical_line",
    "set_axis_marks",
    "show_tracks",
    "plot",
    "save",
]

CANONICAL_TERMS = [
    "group autoscale",
    "group label",
    "track highlight",
    "global highlight",
    "axis mark",
    "global vertical line",
    "feature lane",
    "dual-axis track",
]


def _built_page(relative: str) -> Path:
    build = os.environ.get("PYGV_DOC_BUILD")
    if not build:
        pytest.skip("set PYGV_DOC_BUILD to a built HTML directory")
    return Path(build) / relative


def _html_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8")
    return html.unescape(re.sub(r"<[^>]+>", "", raw))


def _signatures(path: Path) -> dict:
    """Map documented object id -> rendered signature text."""
    raw = path.read_text(encoding="utf-8")
    signatures = {}
    for match in re.finditer(
        r'<dt class="sig sig-object py"[^>]*id="([^"]+)"[^>]*>(.*?)</dt>',
        raw,
        re.S,
    ):
        text = html.unescape(re.sub(r"<[^>]+>", "", match.group(2)))
        signatures[match.group(1)] = re.sub(r"\s+", " ", text).strip()
    return signatures


def test_manifest_commit_is_full_sha():
    assert re.fullmatch(r"[0-9a-f]{40}", MANIFEST["commit"])


def test_manifest_declares_a_known_channel():
    assert MANIFEST["channel"] in {"stable", "development"}
    assert MANIFEST["branch"] in {"main", "dev"}


def test_channel_and_branch_are_consistent():
    expected = {"stable": "main", "development": "dev"}
    assert expected[MANIFEST["channel"]] == MANIFEST["branch"]


@pytest.mark.parametrize(
    "page",
    [
        "index.md",
        "overview.md",
        "installation.md",
        "concepts.md",
        "api/index.md",
        "api/viewer.md",
        "api/utilities.md",
        "provenance.md",
    ],
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


def _toctree_entries(page: str) -> list:
    text = (REPO_ROOT / "docs" / page).read_text(encoding="utf-8")
    block = text.split("```{toctree}", 1)[1].split("```", 1)[0]
    return [
        line.strip()
        for line in block.splitlines()
        if line.strip() and not line.strip().startswith(":")
    ]


def test_index_navigation_order():
    assert _toctree_entries("index.md") == [
        "overview",
        "installation",
        "concepts",
        "api/index",
        "provenance",
    ]


def test_concepts_states_coordinate_convention():
    text = (REPO_ROOT / "docs" / "concepts.md").read_text(encoding="utf-8")
    assert "zero-based" in text
    assert "half-open" in text


@pytest.mark.parametrize("term", CANONICAL_TERMS)
def test_concepts_covers_canonical_term(term):
    text = (REPO_ROOT / "docs" / "concepts.md").read_text(encoding="utf-8").lower()
    assert term in text


@pytest.mark.parametrize("term", CANONICAL_TERMS)
def test_glossary_defines_canonical_term(term):
    text = (REPO_ROOT / "docs" / "overview.md").read_text(encoding="utf-8").lower()
    assert f"\n{term}\n" in text


def test_viewer_reference_uses_autodoc():
    text = (REPO_ROOT / "docs" / "api" / "viewer.md").read_text(encoding="utf-8")
    assert "autoclass:: pygv.viewer.GenomeViewer" in text
    assert ":members:" in text


def test_utilities_reference_uses_autodoc():
    text = (REPO_ROOT / "docs" / "api" / "utilities.md").read_text(encoding="utf-8")
    assert "autofunction:: pygv.utils.check_accessibility" in text
    assert "does **not** probe" in text


# -- Rendered-output tests ---------------------------------------------------


def test_built_site_reports_both_revisions():
    index = _built_page("index.html").read_text(encoding="utf-8")
    provenance = _built_page("provenance.html").read_text(encoding="utf-8")
    assert MANIFEST["commit"][:7] in index
    assert "Build provenance" in provenance


@pytest.mark.parametrize("method", VIEWER_METHODS)
def test_built_viewer_reference_lists_public_method(method):
    raw = _built_page("api/viewer.html").read_text(encoding="utf-8")
    assert f'id="pygv.viewer.GenomeViewer.{method}"' in raw


def test_built_viewer_reference_excludes_private_members():
    raw = _built_page("api/viewer.html").read_text(encoding="utf-8")
    assert 'id="pygv.viewer.GenomeViewer._' not in raw


def test_built_viewer_reference_signatures_and_defaults():
    signatures = _signatures(_built_page("api/viewer.html"))
    assert "hspace=0.2" in signatures["pygv.viewer.GenomeViewer"]
    plot = signatures["pygv.viewer.GenomeViewer.plot"]
    assert "fig_width=8" in plot
    assert "height_scale_factor=1" in plot
    assert "fig_height=None" in plot
    marks = signatures["pygv.viewer.GenomeViewer.set_axis_marks"]
    assert "positions" in marks
    assert "label_rotation=90" in marks
    assert (
        signatures["pygv.viewer.GenomeViewer.set_global_vertical_line"]
        == "set_global_vertical_line(position: int, color='red', alpha=0.8, "
        "line_width=1.5, line_style='-', margin_frac=0.02)#"
    )


def test_built_utilities_exposes_check_accessibility():
    signatures = _signatures(_built_page("api/utilities.html"))
    signature = signatures["pygv.utils.check_accessibility"]
    assert "file_path: str" in signature
    assert "allow_remote: bool = False" in signature
    assert "raise_except: bool = True" in signature


def test_built_utilities_does_not_overclaim():
    text = _html_text(_built_page("api/utilities.html")).lower()
    assert "does not probe a remote endpoint" in text
    assert "reachability" not in text
    assert "probes the endpoint" not in text


def test_built_concepts_page_uses_canonical_terms():
    text = _html_text(_built_page("concepts.html")).lower()
    assert "zero-based" in text
    assert "half-open" in text
    for term in CANONICAL_TERMS:
        assert term in text


def test_built_concepts_links_to_api_reference():
    raw = _built_page("concepts.html").read_text(encoding="utf-8")
    assert 'href="api/index.html"' in raw


def test_built_api_viewer_links_to_concepts():
    raw = _built_page("api/viewer.html").read_text(encoding="utf-8")
    assert 'href="../concepts.html"' in raw


def test_built_api_index_links_to_children():
    raw = _built_page("api/index.html").read_text(encoding="utf-8")
    assert 'href="viewer.html"' in raw
    assert 'href="utilities.html"' in raw
