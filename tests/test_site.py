import html
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((REPO_ROOT / "code-ref.json").read_text(encoding="utf-8"))

REPRESENTATIVE_EXAMPLES = [
    "plot_bed",
    "plot_bam_arc_reads",
    "plot_group_autoscale",
    "plot_gwas",
]

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


def _build_dir() -> Path:
    build = os.environ.get("PYGV_DOC_BUILD")
    if not build:
        pytest.skip("set PYGV_DOC_BUILD to a built HTML directory")
    return Path(build)


def _built_page(relative: str) -> Path:
    return _build_dir() / relative


def _gallery_revision_dir() -> Path:
    build = _build_dir()
    revisions = sorted(p for p in (build / "gallery").glob("*/*") if p.is_dir())
    assert len(revisions) == 1, f"expected one gallery revision, found {revisions}"
    return revisions[0]


def _paired_checkout() -> Path | None:
    """Locate the code checkout the gallery was generated from, if available."""
    candidates = []
    env = os.environ.get("PYGV_CODE_DIR")
    if env:
        candidates.append(Path(env))
    candidates.append(REPO_ROOT / ".build" / "code")
    candidates.append(REPO_ROOT.parent / "code")
    for candidate in candidates:
        if (candidate / "examples").is_dir():
            return candidate
    return None


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
        "gallery.md",
        "third-party-notices.md",
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
        "gallery",
        "provenance",
    ]


def test_gallery_landing_page_uses_glob_and_introduces_the_gallery():
    text = (REPO_ROOT / "docs" / "gallery.md").read_text(encoding="utf-8")
    assert "Complete Gallery" in text
    assert ":glob:" in text
    assert "gallery/*/*/index" in text
    assert "third-party-notices" in text
    assert "pinned code checkout" in text or "paired checkout" in text
    assert "requirements.txt" in text


def test_notices_page_renders_the_canonical_notices():
    text = (REPO_ROOT / "docs" / "third-party-notices.md").read_text(encoding="utf-8")
    assert "include} ../THIRD_PARTY_NOTICES.md" in text
    assert (REPO_ROOT / "THIRD_PARTY_NOTICES.md").is_file()


def test_generated_gallery_output_is_not_tracked():
    result = subprocess.run(
        ["git", "ls-files", "docs/gallery"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == ""
    assert "docs/gallery/" in (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")


def test_example_fixtures_are_not_copied_into_the_docs_tree():
    docs_examples = REPO_ROOT / "docs" / "_examples"
    assert sorted(path.name for path in docs_examples.iterdir()) == ["quickstart.py"]
    assert not any((REPO_ROOT / "docs" / name).exists() for name in ("data", "examples"))


def test_gallery_cache_identity_includes_revision_and_dependency_lock():
    spec = importlib.util.spec_from_file_location(
        "build_docs", REPO_ROOT / "tools" / "build_docs.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    digest = hashlib.sha256(
        (REPO_ROOT / "requirements.txt").read_bytes()
    ).hexdigest()[:12]
    assert module.dependency_lock_digest() == digest

    path = module.gallery_dir(MANIFEST["channel"], MANIFEST["commit"], digest)
    assert MANIFEST["commit"][:12] in path
    assert digest in path


def test_conf_reads_examples_from_the_paired_checkout():
    text = (REPO_ROOT / "docs" / "conf.py").read_text(encoding="utf-8")
    assert 'Path(_code_dir) / "examples"' in text
    assert "PYGV_GALLERY_DIR" in text
    assert '"download_all_examples": True' in text


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


# -- Rendered gallery --------------------------------------------------------


def test_built_gallery_has_one_page_per_checkout_example():
    pages = sorted(path.name for path in _gallery_revision_dir().glob("plot_*.html"))
    checkout = _paired_checkout()
    if checkout is None:
        pytest.skip("paired code checkout not available to count examples")
    scripts = sorted(path.name for path in (checkout / "examples").glob("plot_*.py"))
    assert scripts, "no plot_*.py examples found in the paired checkout"
    assert len(pages) == len(scripts)
    assert {name[: -len(".html")] for name in pages} == {
        name[: -len(".py")] for name in scripts
    }


def test_built_gallery_uses_a_single_clean_revision_directory():
    build = _build_dir()
    revisions = sorted(path.name for path in (build / "gallery").glob("*/*"))
    assert len(revisions) == 1
    revision = revisions[0]
    assert MANIFEST["commit"][:12] in revision
    lock = hashlib.sha256(
        (REPO_ROOT / "requirements.txt").read_bytes()
    ).hexdigest()[:12]
    assert revision.endswith(lock)


@pytest.mark.parametrize("name", REPRESENTATIVE_EXAMPLES)
def test_built_gallery_example_renders_an_image(name):
    build = _build_dir()
    raw = (_gallery_revision_dir() / f"{name}.html").read_text(encoding="utf-8")
    image = build / "_images" / f"sphx_glr_{name}_001.png"
    assert image.is_file() and image.stat().st_size > 0
    assert f"sphx_glr_{name}_001.png" in raw
    assert "<img" in raw


@pytest.mark.parametrize("name", REPRESENTATIVE_EXAMPLES)
def test_built_gallery_example_exposes_script_downloads(name):
    build = _build_dir()
    raw = (_gallery_revision_dir() / f"{name}.html").read_text(encoding="utf-8")
    py = re.search(r"_downloads/[0-9a-f]+/" + re.escape(name) + r"\.py", raw)
    assert py, f"no .py download link for {name}"
    assert (build / py.group(0)).is_file()
    zips = re.findall(r"_downloads/[0-9a-f]+/" + re.escape(name) + r"\.zip", raw)
    assert zips, f"no .zip download link for {name}"
    assert (build / zips[0]).is_file()


def test_built_gallery_is_reachable_from_navigation():
    index = _built_page("index.html").read_text(encoding="utf-8")
    assert 'href="gallery.html"' in index

    landing = _built_page("gallery.html").read_text(encoding="utf-8")
    assert "Complete Gallery" in landing
    generated = re.search(r'href="(gallery/[^"]+/index\.html)"', landing)
    assert generated, "gallery landing page does not link to the generated index"
    assert (_build_dir() / generated.group(1)).is_file()


def test_built_gallery_landing_links_to_third_party_notices():
    landing = _built_page("gallery.html").read_text(encoding="utf-8")
    assert 'href="third-party-notices.html"' in landing
    notices = _html_text(_built_page("third-party-notices.html"))
    for marker in ("Sphinx-Gallery", "ENCODE", "GENCODE", "GWAS"):
        assert marker in notices

