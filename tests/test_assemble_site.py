"""Tests for ``tools/assemble_site.py``.

These tests use synthetic channel fixture directories, so they need no network,
no Sphinx build, and no external service. They pin the assembly contract:
stable at the artifact root, development under ``/dev/``, one fresh aggregate
that always contains both channels, per-channel provenance, ``llms.txt`` and
Markdown alternatives, and a loud failure for incomplete or unsafe input.
"""

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL = REPO_ROOT / "tools" / "assemble_site.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("assemble_site", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


assemble_site = _load_tool()
AssemblyError = assemble_site.AssemblyError


def _write_channel(root: Path, channel: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)

    (root / "index.html").write_text(
        "<html><head>"
        '<link rel="alternate" type="text/markdown" href="index.md" />'
        '<link rel="llms" type="text/plain" href="llms.txt" />'
        f"</head><body><article><h1>{channel}</h1></article></body></html>",
        encoding="utf-8",
    )
    (root / "index.md").write_text(
        f"# PyGV {channel}\n\n" + "Index content. " * 20 + "\n", encoding="utf-8"
    )
    (root / "provenance.html").write_text(
        "<article><table><tr><th>Item</th><th>Value</th></tr>"
        f"<tr><td>Documentation channel</td><td>{channel}</td></tr>"
        "<tr><td>Code branch</td><td>paired</td></tr></table></article>",
        encoding="utf-8",
    )
    (root / "provenance.md").write_text(
        f"| Item | Value |\n| --- | --- |\n| Documentation channel | {channel} |\n\n"
        + "Provenance content. " * 20
        + "\n",
        encoding="utf-8",
    )
    (root / "overview.html").write_text(
        "<article><h1>Overview</h1></article>", encoding="utf-8"
    )
    (root / "overview.md").write_text(
        "# Overview\n\n" + "Overview content. " * 20 + "\n", encoding="utf-8"
    )

    # Non-canonical plumbing: must not require a Markdown alternative.
    (root / "search.html").write_text("<html>search</html>", encoding="utf-8")
    static = root / "_static"
    static.mkdir()
    (static / "theme.html").write_text("<html>theme</html>", encoding="utf-8")

    (root / "llms.txt").write_text(
        "# PyGV\n\n"
        "> Synthetic channel summary.\n\n"
        f"- Documentation channel: {channel}; describes the synthetic build.\n\n"
        "## Start here\n\n"
        "- [Documentation index](index.md): entry point.\n"
        "- [Overview](overview.md): overview.\n"
        "- [Build provenance](provenance.md): provenance.\n",
        encoding="utf-8",
    )
    return root


@pytest.fixture
def channels(tmp_path):
    stable = _write_channel(tmp_path / "stable", "stable")
    development = _write_channel(tmp_path / "development", "development")
    return stable, development


def test_stable_is_at_the_root_and_development_is_under_dev(channels, tmp_path):
    stable, development = channels
    out = tmp_path / "site"

    assemble_site.assemble(stable, development, out)

    assert (out / "index.html").is_file()
    assert (out / "llms.txt").is_file()
    assert (out / "dev" / "index.html").is_file()
    assert (out / "dev" / "llms.txt").is_file()
    assert (out / "dev" / "overview.md").is_file()


def test_both_channels_are_always_present(channels, tmp_path):
    stable, development = channels
    out = tmp_path / "site"

    assemble_site.assemble(stable, development, out)

    assert (out / "provenance.html").is_file()
    assert (out / "dev" / "provenance.html").is_file()
    assert "stable" in (out / "provenance.html").read_text(encoding="utf-8")
    assert "development" in (out / "dev" / "provenance.html").read_text(
        encoding="utf-8"
    )


def test_a_single_channel_cannot_erase_the_other(channels, tmp_path):
    stable, development = channels
    out = tmp_path / "site"

    assemble_site.assemble(stable, development, out)
    assert (out / "dev" / "index.html").is_file()

    # A second assembly from the same two channels rebuilds the development
    # subtree from scratch instead of dropping it.
    assemble_site.assemble(stable, development, out)
    assert (out / "dev" / "index.html").is_file()
    assert (out / "dev" / "llms.txt").is_file()


def test_each_channel_has_its_own_provenance_and_llms(channels, tmp_path):
    stable, development = channels
    out = tmp_path / "site"

    assemble_site.assemble(stable, development, out)

    assert "Documentation channel: stable" in (out / "llms.txt").read_text(
        encoding="utf-8"
    )
    assert "Documentation channel: development" in (
        out / "dev" / "llms.txt"
    ).read_text(encoding="utf-8")


def test_markdown_alternatives_are_present_for_both_channels(channels, tmp_path):
    stable, development = channels
    out = tmp_path / "site"

    assemble_site.assemble(stable, development, out)

    for base in (out, out / "dev"):
        for page in ("index", "overview", "provenance"):
            markdown = base / f"{page}.md"
            assert markdown.is_file()
            assert markdown.read_text(encoding="utf-8").strip()


def test_output_starts_fresh_and_drops_stale_files(channels, tmp_path):
    stable, development = channels
    out = tmp_path / "site"
    (out / "dev").mkdir(parents=True)
    (out / "stale.html").write_text("old", encoding="utf-8")
    (out / "dev" / "stale.html").write_text("old", encoding="utf-8")

    assemble_site.assemble(stable, development, out)

    assert not (out / "stale.html").exists()
    assert not (out / "dev" / "stale.html").exists()
    assert (out / "dev" / "index.html").is_file()


def test_missing_channel_directory_fails(channels, tmp_path):
    stable, _ = channels
    with pytest.raises(AssemblyError, match="missing"):
        assemble_site.assemble(stable, tmp_path / "absent", tmp_path / "site")


@pytest.mark.parametrize(
    "remove",
    ["llms.txt", "index.html", "index.md", "provenance.html", "provenance.md"],
)
def test_incomplete_channel_fails(channels, tmp_path, remove):
    stable, development = channels
    (development / remove).unlink()
    with pytest.raises(AssemblyError):
        assemble_site.assemble(stable, development, tmp_path / "site")


def test_missing_markdown_alternative_fails(channels, tmp_path):
    stable, development = channels
    (development / "overview.md").unlink()
    with pytest.raises(AssemblyError, match="Markdown alternative"):
        assemble_site.assemble(stable, development, tmp_path / "site")


def test_wrong_channel_marker_fails(channels, tmp_path):
    stable, development = channels
    (development / "llms.txt").write_text(
        "# PyGV\n\n- Documentation channel: stable\n", encoding="utf-8"
    )
    with pytest.raises(AssemblyError, match="does not declare"):
        assemble_site.assemble(stable, development, tmp_path / "site")


def test_unresolved_llms_link_fails(channels, tmp_path):
    stable, development = channels
    (development / "llms.txt").write_text(
        "# PyGV\n\n- Documentation channel: development\n\n"
        "- [Broken](missing.md): does not exist.\n",
        encoding="utf-8",
    )
    with pytest.raises(AssemblyError, match="does not resolve"):
        assemble_site.assemble(stable, development, tmp_path / "site")


def test_absolute_llms_link_fails(channels, tmp_path):
    stable, development = channels
    (development / "llms.txt").write_text(
        "# PyGV\n\n- Documentation channel: development\n\n"
        "- [External](https://example.com/index.md): not channel relative.\n",
        encoding="utf-8",
    )
    with pytest.raises(AssemblyError, match="channel-relative"):
        assemble_site.assemble(stable, development, tmp_path / "site")


def test_cname_is_rejected(channels, tmp_path):
    stable, development = channels
    (stable / "CNAME").write_text("docs.example.com\n", encoding="utf-8")
    with pytest.raises(AssemblyError, match="CNAME"):
        assemble_site.assemble(stable, development, tmp_path / "site")


def test_historical_version_directory_is_rejected(channels, tmp_path):
    stable, development = channels
    (stable / "v1.0").mkdir()
    (stable / "v1.0" / "index.html").write_text("<html></html>", encoding="utf-8")
    with pytest.raises(AssemblyError, match="version directory"):
        assemble_site.assemble(stable, development, tmp_path / "site")


def test_stable_channel_must_not_contain_a_dev_subtree(channels, tmp_path):
    stable, development = channels
    (stable / "dev").mkdir()
    with pytest.raises(AssemblyError, match="top-level dev/"):
        assemble_site.assemble(stable, development, tmp_path / "site")


def test_combined_artifact_has_no_cname_or_version_directories(channels, tmp_path):
    stable, development = channels
    out = tmp_path / "site"

    assemble_site.assemble(stable, development, out)

    assert not [path for path in out.rglob("*") if path.name.lower() == "cname"]
    version_re = assemble_site.VERSION_DIR_RE
    for base in (out, out / "dev"):
        for child in base.iterdir():
            assert not (child.is_dir() and version_re.match(child.name))


def test_cli_round_trip(channels, tmp_path, capsys):
    stable, development = channels
    out = tmp_path / "site"

    code = assemble_site.main(
        [
            "--stable",
            str(stable),
            "--development",
            str(development),
            "--outdir",
            str(out),
        ]
    )

    assert code == 0
    assert "Assembled" in capsys.readouterr().out
    assert (out / "dev" / "index.html").is_file()


def test_cli_reports_failure(channels, tmp_path, capsys):
    stable, _ = channels
    out = tmp_path / "site"

    code = assemble_site.main(
        [
            "--stable",
            str(stable),
            "--development",
            str(tmp_path / "absent"),
            "--outdir",
            str(out),
        ]
    )

    assert code == 1
    assert "error:" in capsys.readouterr().err
    assert not out.exists()
