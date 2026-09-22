import hashlib
import html
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

GLOSSARY_TERMS = CANONICAL_TERMS + [
    "gwas marker",
    "bedpe link",
    "significance line",
]

TRACK_EXPORTS = [
    "Track",
    "AnnotationTrack",
    "NumericalTrack",
    "DynamicValueTrack",
    "DualAxisTrack",
    "CoverageTrack",
    "CollapsedReadTrack",
    "SplicedReadTrack",
    "StrandSpecificCoverageTrack",
    "ReadArcTrack",
    "BedTrack",
    "BedPETrack",
    "ConnectionArcTrack",
    "UCSCMutationTrack",
    "BigBed6Track",
    "BigWigTrack",
    "OverlayingTrack",
    "PairedStrandSpecificTrack",
    "PairedStrandSpecificTracks",
    "PairedStrandlessTrack",
    "GtfTrack",
    "GWASTrack",
    "LogoTrack",
    "DynseqTrack",
]

# One representative per track family, sampled in the rendered reference.
TRACK_FAMILIES = {
    "base": "Track",
    "annotation": "BedTrack",
    "alignment": "CoverageTrack",
    "numerical signal": "BigWigTrack",
    "paired/overlay": "PairedStrandSpecificTrack",
    "connections": "BedPETrack",
    "sequence": "LogoTrack",
    "gwas": "GWASTrack",
    "dual-axis": "DualAxisTrack",
}

LIFECYCLE_HOOKS = ["_pre_plot_hook", "_draw_track", "_post_plot_hook"]


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
        "track-guide.md",
        "data-formats.md",
        "api/index.md",
        "api/viewer.md",
        "api/tracks.md",
        "api/utilities.md",
        "gallery.md",
        "changelog.md",
        "third-party-notices.md",
        "provenance.md",
    ],
)
def test_authored_page_exists(page):
    assert (REPO_ROOT / "docs" / page).is_file()


def test_quickstart_runs(tmp_path):
    script = REPO_ROOT / "docs" / "_examples" / "quickstart.py"
    # The build imports the paired checkout directly (never a floating
    # installed distribution), so the published snippet must be executed with
    # that same checkout first on the import path.
    checkout = _paired_checkout()
    assert checkout is not None, "paired code checkout is not available"
    output = tmp_path / "quickstart.png"
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"
    env["PYGV_QUICKSTART_OUT"] = str(output)
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(checkout) + (
        os.pathsep + existing if existing else ""
    )
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
        "track-guide",
        "api/index",
        "data-formats",
        "gallery",
        "changelog",
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


@pytest.mark.parametrize("term", GLOSSARY_TERMS)
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


@pytest.mark.parametrize("name", TRACK_EXPORTS)
def test_tracks_reference_documents_every_export(name):
    text = (REPO_ROOT / "docs" / "api" / "tracks.md").read_text(encoding="utf-8")
    assert f".. autoclass:: pygv.tracks.{name}\n" in text


def test_tracks_reference_requests_inherited_fields_and_hooks():
    text = (REPO_ROOT / "docs" / "api" / "tracks.md").read_text(encoding="utf-8")
    assert ":inherited-members:" in text
    assert ":private-members: _pre_plot_hook, _draw_track, _post_plot_hook" in text


def test_tracks_reference_lists_no_other_private_members():
    text = (REPO_ROOT / "docs" / "api" / "tracks.md").read_text(encoding="utf-8")
    private = set(re.findall(r"(?<![\w:])_([A-Za-z]\w*)", text))
    assert private <= {"pre_plot_hook", "draw_track", "post_plot_hook"}


def test_track_guide_covers_every_family():
    text = (REPO_ROOT / "docs" / "track-guide.md").read_text(encoding="utf-8")
    for heading in (
        "Annotation tracks",
        "Alignment tracks",
        "Numerical signal tracks",
        "Paired and overlay compositions",
        "Connections",
        "Sequence tracks",
        "GWAS",
    ):
        assert heading in text
    for family in TRACK_FAMILIES.values():
        assert f"pygv.tracks.{family}" in text


def test_track_guide_prefers_canonical_paired_name_and_flags_alias():
    text = (REPO_ROOT / "docs" / "track-guide.md").read_text(encoding="utf-8")
    assert "PairedStrandSpecificTrack` is the **canonical**" in text
    assert "PairedStrandSpecificTracks` is a **retained compatibility" in text
    for alias in ("inward_ticks", "transformation", "draw_y_independently", "flip"):
        assert alias in text


def test_data_formats_documents_coordinates_sources_and_indexing():
    text = (REPO_ROOT / "docs" / "data-formats.md").read_text(encoding="utf-8").lower()
    assert "zero-based" in text
    assert "half-open" in text
    for marker in ("remote", "index", "bam", "bigwig", "bed6+"):
        assert marker in text


def test_changelog_documents_migration():
    text = (REPO_ROOT / "docs" / "changelog.md").read_text(encoding="utf-8")
    assert "Migration checklist" in text
    assert "layout_height()" in text
    assert "Python 3.10" in text


def test_license_declarations_are_consistently_gpl_3_or_later():
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'license = "GPL-3.0-or-later"' in pyproject
    assert 'license-files = ["LICENSE", "THIRD_PARTY_NOTICES.md"]' in pyproject

    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "GPL-3.0-or-later" in readme

    notices = (REPO_ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    assert "GPL-3.0-or-later" in notices

    license_text = (REPO_ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "GNU GENERAL PUBLIC LICENSE" in license_text
    assert "Version 3, 29 June 2007" in license_text
    assert "MIT License" not in license_text


def test_third_party_notices_cover_theme_assets_and_data():
    notices = (REPO_ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    for marker in (
        "Sphinx",
        "MyST-Parser",
        "PyData Sphinx Theme",
        "Sphinx-Gallery",
        "Matplotlib",
        "ENCODE",
        "GENCODE",
        "GWAS",
    ):
        assert marker in notices, marker


def test_track_guide_states_the_gwas_contract():
    text = (REPO_ROOT / "docs" / "track-guide.md").read_text(encoding="utf-8")
    assert "end - start == 1" in text
    assert "raw" in text.lower()
    assert "-log10" in text
    assert "RuntimeWarning" in text
    assert "significance_lines" in text
    assert "tracked separately" in text
    assert "not supported behavior" in text


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
    assert 'href="tracks.html"' in raw
    assert 'href="utilities.html"' in raw


def _tracks_raw() -> str:
    return _built_page("api/tracks.html").read_text(encoding="utf-8")


def _tracks_text() -> str:
    return _html_text(_built_page("api/tracks.html")).lower()


def _rendered_private_member_names(raw: str) -> set:
    """Names of documented underscore members across the tracks reference."""
    return set(
        re.findall(r'id="pygv\.tracks\.\w+\.(_\w+)"', raw)
    )


@pytest.mark.parametrize("name", TRACK_EXPORTS)
def test_built_tracks_reference_lists_every_export(name):
    assert f'id="pygv.tracks.{name}"' in _tracks_raw()


@pytest.mark.parametrize("family,representative", sorted(TRACK_FAMILIES.items()))
def test_built_tracks_reference_samples_each_family(family, representative):
    raw = _tracks_raw()
    assert f'id="pygv.tracks.{representative}"' in raw
    assert "Configuration fields" in raw


def test_built_tracks_reference_shows_inherited_fields_and_descriptions():
    text = _tracks_text()
    for field in ("inward_yticks", "data_transform", "min_val", "show_range"):
        assert field in text
    for description in (
        "alpha of patches",
        "path to the bam file",
        "path to the annotation file",
        "height of patches",
    ):
        assert description in text


def test_built_tracks_reference_shows_compatibility_aliases():
    text = _tracks_text()
    for alias in ("inward_ticks", "transformation", "draw_y_independently", "flip"):
        assert alias in text


def test_built_tracks_reference_shows_literals_and_defaults():
    text = _tracks_text()
    assert "literal['line', 'bar']" in text
    assert "literal['expanded', 'collapsed']" in text
    assert "positivefloat = 1" in text


def test_built_tracks_reference_exposes_only_three_lifecycle_hooks():
    rendered = _rendered_private_member_names(_tracks_raw())
    assert set(LIFECYCLE_HOOKS) <= rendered
    assert rendered <= set(LIFECYCLE_HOOKS)


def test_built_tracks_reference_excludes_other_private_members():
    raw = _tracks_raw()
    for private in (
        'id="pygv.tracks.GWASTrack._get"',
        'id="pygv.tracks.GWASTrack._validate_and_collect"',
        'id="pygv.tracks.CoverageTrack._bam"',
        'id="pygv.tracks.BedPETrack._normalize_highlight_link"',
        "_GenericBamTrack",
        "_GenericNumericalBamTrack",
        "_validate_color",
        "model_fields",
    ):
        assert private not in raw


def test_built_tracks_reference_links_from_track_guide():
    raw = _built_page("track-guide.html").read_text(encoding="utf-8")
    assert 'href="api/tracks.html"' in raw


def test_built_track_guide_covers_each_family():
    text = _html_text(_built_page("track-guide.html")).lower()
    for phrase in (
        "annotation tracks",
        "alignment tracks",
        "numerical signal tracks",
        "paired and overlay compositions",
        "connections",
        "sequence tracks",
        "gwas",
    ):
        assert phrase in text


def test_built_gwas_contract_language():
    text = _html_text(_built_page("track-guide.html"))
    assert "end - start == 1" in text
    assert "raw" in text.lower()
    assert "-log10(p)" in text
    assert "RuntimeWarning" in text
    assert "significance_lines" in text
    assert "tracked separately" in text
    assert "not supported behavior" in text


def test_built_data_formats_documents_coordinates_and_indexing():
    text = _html_text(_built_page("data-formats.html")).lower()
    assert "zero-based" in text
    assert "half-open" in text
    assert "check_accessibility" in text
    assert "indexing expectations" in text


def test_built_changelog_documents_migration():
    text = _html_text(_built_page("changelog.html"))
    assert "Migration checklist" in text
    assert "layout_height()" in text


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


# -- Agent-readable artifacts ------------------------------------------------

AGENT_EXCLUDED_NAMES = {
    "search.html",
    "genindex.html",
    "py-modindex.html",
    "modindex.html",
    "404.html",
}
AGENT_EXCLUDED_PARTS = {"_static", "_sources", "_downloads", "_images"}

UNRESOLVED_DIRECTIVE = re.compile(
    r"\{autoclass\}|\{autofunction\}|\{automodule\}|\{eval-rst\}|"
    r"\{toctree\}|\{literalinclude\}|\{admonition\}|"
    r"\.\.\s+(?:auto(?:class|function|module)|plot)::"
)

PRIVATE_MARKERS = ["DignoMor/PyGV-spec", "release-map", ".agents"]


def _canonical_html_pages() -> list:
    build = _build_dir()
    pages = []
    for path in sorted(build.rglob("*.html")):
        rel = path.relative_to(build)
        if rel.name in AGENT_EXCLUDED_NAMES:
            continue
        if any(part in AGENT_EXCLUDED_PARTS for part in rel.parts):
            continue
        pages.append(rel)
    return pages


def _markdown_links(text: str) -> list:
    return re.findall(r"\]\(([^)\s]+)\)", text)


def test_every_canonical_page_displays_the_revision_pairing():
    build = _build_dir()
    short = MANIFEST["commit"][:7]
    pages = _canonical_html_pages()
    assert pages, "no canonical HTML pages found"
    for rel in pages:
        raw = (build / rel).read_text(encoding="utf-8")
        assert 'class="footer-provenance"' in raw, f"{rel} has no footer provenance"
        assert short in raw, f"{rel} does not name the paired code commit"


def test_each_channel_root_has_exactly_one_llms_txt():
    build = _build_dir()
    found = sorted(path.relative_to(build).as_posix() for path in build.rglob("llms.txt"))
    assert found == ["llms.txt"]


def test_llms_txt_states_project_install_import_coordinates_and_version():
    text = (_build_dir() / "llms.txt").read_text(encoding="utf-8")
    lines = text.splitlines()
    assert lines[0] == "# PyGV"
    assert lines[2].startswith("> "), "llms.txt must open with a concise summary"
    assert "pip install GenomeViewer" in text
    assert "`pygv`" in text and "from pygv.viewer import GenomeViewer" in text
    assert "zero-based" in text and "half-open" in text
    assert "Documentation channel:" in text
    assert MANIFEST["commit"][:7] in text

    provenance = re.sub(
        r"\s+",
        " ",
        _html_text(_built_page("provenance.html")),
    )
    version = re.search(r"GenomeViewer version (\S+)", provenance)
    assert version, "could not read the rendered GenomeViewer version"
    assert version.group(1) in text


def test_llms_txt_groups_and_describes_canonical_resources():
    text = (_build_dir() / "llms.txt").read_text(encoding="utf-8")
    for section in (
        "## Start here",
        "## API reference",
        "## Examples",
        "## Project metadata",
    ):
        assert section in text
    for line in text.splitlines():
        if line.startswith("- [") and line.endswith("."):
            assert "): " in line, f"undescribed llms.txt entry: {line}"


def test_llms_txt_links_resolve_to_agent_readable_markdown():
    build = _build_dir()
    text = (build / "llms.txt").read_text(encoding="utf-8")
    links = _markdown_links(text)
    assert links
    for target in links:
        assert not target.startswith(("http://", "https://", "/")), target
        resolved = (build / target).resolve()
        assert resolved.is_file(), f"unresolved llms.txt link: {target}"
        assert resolved.suffix == ".md", target
        body = resolved.read_text(encoding="utf-8")
        assert len(body.strip()) > 200, f"trivial markdown target: {target}"
        assert not UNRESOLVED_DIRECTIVE.search(body), target


def test_no_llms_full_txt_is_emitted():
    assert not list(_build_dir().rglob("llms-full*"))


def test_every_canonical_page_has_a_markdown_alternative():
    build = _build_dir()
    pages = _canonical_html_pages()
    assert pages, "no canonical HTML pages found"
    for rel in pages:
        markdown = (build / rel).with_suffix(".md")
        assert markdown.is_file(), f"missing markdown alternative for {rel}"
        assert markdown.read_text(encoding="utf-8").strip(), rel


def test_non_canonical_pages_have_no_markdown_alternative():
    build = _build_dir()
    for name in ("search.html", "genindex.html"):
        assert not (build / name).with_suffix(".md").exists()


def test_every_canonical_page_advertises_markdown_and_llms():
    build = _build_dir()
    for rel in _canonical_html_pages():
        raw = (build / rel).read_text(encoding="utf-8")
        alternate = re.search(
            r'<link rel="alternate" type="text/markdown" href="([^"]+)"', raw
        )
        assert alternate, f"{rel} does not advertise a markdown alternate"
        advertised = (build / rel).parent / alternate.group(1)
        assert advertised.resolve() == (build / rel).with_suffix(".md").resolve()

        llms = re.search(r'<link rel="llms"[^>]*href="([^"]+)"', raw)
        assert llms, f"{rel} does not advertise llms.txt"
        assert (
            (build / rel).parent / llms.group(1)
        ).resolve() == (build / "llms.txt").resolve()
        assert "llms.txt" in raw


def test_markdown_alternatives_carry_expanded_api_content():
    build = _build_dir()
    viewer = (build / "api" / "viewer.md").read_text(encoding="utf-8")
    assert "hspace=0.2" in viewer
    assert "fig_width=8" in viewer
    assert "set_global_vertical_line" in viewer
    assert "Genome Viewer" in viewer

    tracks = (build / "api" / "tracks.md").read_text(encoding="utf-8")
    assert "Configuration fields" in tracks
    for field in ("inward_yticks", "inward_ticks", "show_mode"):
        assert field in tracks
    for description in ("Alpha of patches", "Path to the BAM file"):
        assert description in tracks
    assert "Literal['line', 'bar']" in tracks

    utilities = (build / "api" / "utilities.md").read_text(encoding="utf-8")
    assert "check_accessibility" in utilities
    assert "allow_remote" in utilities
    assert "does **not** probe a remote endpoint" in utilities


def test_markdown_alternatives_have_no_unresolved_directives():
    build = _build_dir()
    for rel in _canonical_html_pages():
        body = (build / rel).with_suffix(".md").read_text(encoding="utf-8")
        found = UNRESOLVED_DIRECTIVE.search(body)
        assert not found, f"{rel} still contains directive {found.group(0)!r}"


def test_agent_artifacts_exclude_private_planning_material():
    build = _build_dir()
    artifacts = [build / "llms.txt"]
    artifacts.extend(
        (build / rel).with_suffix(".md") for rel in _canonical_html_pages()
    )
    for artifact in artifacts:
        body = artifact.read_text(encoding="utf-8")
        for marker in PRIVATE_MARKERS:
            assert marker not in body, f"{marker} leaked into {artifact.name}"
        assert not re.search(r"\bADR\b", body), f"ADR marker in {artifact.name}"

