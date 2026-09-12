#!/usr/bin/env python3
"""Assemble the two-channel PyGV GitHub Pages artifact.

The Pages site publishes two documentation channels from one atomic artifact:

* the **stable** channel at the artifact root, built from the documentation and
  code ``main`` pair; and
* the **development** channel at ``/dev/``, built from the documentation and
  code ``dev`` pair.

Each channel is built independently by ``tools/build_docs.py``. This tool
combines two already-built channel directories into one fresh aggregate so a
single-channel build can never erase the other channel.

Usage::

    python tools/assemble_site.py \
        --stable build/stable \
        --development build/development \
        --outdir build/site

The aggregate always starts from a clean output directory. Before anything is
copied each channel is validated for its channel provenance, ``llms.txt``, and
Markdown alternatives; after assembly the aggregate is validated again so that
both channels are present. The tool never writes a ``CNAME`` or a historical
version directory (a top-level ``v1``/``1.2.3`` style folder).
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

STABLE_CHANNEL = "stable"
DEVELOPMENT_CHANNEL = "development"
DEVELOPMENT_PREFIX = "dev"

# Navigation and asset trees that are not canonical human-facing pages and
# therefore do not need a Markdown alternative. These mirror the exclusion set
# used by the ``agent_artifacts`` Sphinx extension.
EXCLUDED_NAMES = {
    "search.html",
    "genindex.html",
    "py-modindex.html",
    "modindex.html",
    "404.html",
}
EXCLUDED_PARTS = {"_static", "_sources", "_downloads", "_images"}

CNAME_NAME = "cname"
VERSION_DIR_RE = re.compile(r"^v?\d+(?:\.\d+)*$")
MARKDOWN_LINK_RE = re.compile(r"\]\(([^)\s]+)\)")


class AssemblyError(Exception):
    """Raised when a channel or the assembled aggregate is not publishable."""


def _is_canonical(rel: Path) -> bool:
    if rel.name in EXCLUDED_NAMES:
        return False
    return not any(part in EXCLUDED_PARTS for part in rel.parts)


def _canonical_pages(root: Path) -> list[Path]:
    pages = []
    for path in sorted(root.rglob("*.html")):
        rel = path.relative_to(root)
        if _is_canonical(rel):
            pages.append(rel)
    return pages


def _is_forbidden_version_dir(name: str) -> bool:
    return bool(VERSION_DIR_RE.match(name))


def _top_level_bases(root: Path) -> list[Path]:
    bases = [root]
    development = root / DEVELOPMENT_PREFIX
    if development.is_dir():
        bases.append(development)
    return bases


def _find_cname(root: Path) -> list[Path]:
    return [path for path in root.rglob("*") if path.name.lower() == CNAME_NAME]


def _find_version_dirs(root: Path) -> list[Path]:
    found = []
    for base in _top_level_bases(root):
        for child in base.iterdir():
            if child.is_dir() and _is_forbidden_version_dir(child.name):
                found.append(child)
    return found


def _assert_no_forbidden_paths(root: Path, label: str) -> None:
    cnames = _find_cname(root)
    if cnames:
        raise AssemblyError(
            f"{label} contains a custom-domain CNAME file: "
            f"{cnames[0].relative_to(root).as_posix()}"
        )
    versions = _find_version_dirs(root)
    if versions:
        raise AssemblyError(
            f"{label} contains a historical version directory: "
            f"{versions[0].relative_to(root).as_posix()}"
        )


def _validate_llms_links(channel_root: Path, channel: str) -> None:
    llms = channel_root / "llms.txt"
    links = MARKDOWN_LINK_RE.findall(llms.read_text(encoding="utf-8"))
    if not links:
        raise AssemblyError(f"{channel} llms.txt has no Markdown links")
    for target in links:
        if target.startswith(("http://", "https://", "/")):
            raise AssemblyError(
                f"{channel} llms.txt link must be channel-relative: {target}"
            )
        resolved = (channel_root / target).resolve()
        if not resolved.is_file():
            raise AssemblyError(
                f"{channel} llms.txt link does not resolve: {target}"
            )
        if resolved.suffix != ".md":
            raise AssemblyError(
                f"{channel} llms.txt link is not a Markdown alternate: {target}"
            )
        if not resolved.read_text(encoding="utf-8").strip():
            raise AssemblyError(f"{channel} llms.txt link is empty: {target}")


def validate_channel(channel_root: Path, channel: str) -> None:
    """Fail loudly unless ``channel_root`` is a complete built channel."""

    if not channel_root.is_dir():
        raise AssemblyError(f"{channel} channel directory is missing: {channel_root}")

    _assert_no_forbidden_paths(channel_root, f"{channel} channel")

    if (channel_root / DEVELOPMENT_PREFIX).is_dir():
        raise AssemblyError(
            f"{channel} channel already contains a top-level "
            f"{DEVELOPMENT_PREFIX}/ subtree"
        )

    llms = channel_root / "llms.txt"
    if not llms.is_file() or not llms.read_text(encoding="utf-8").strip():
        raise AssemblyError(f"{channel} channel is missing llms.txt")

    marker = f"Documentation channel: {channel}"
    if marker not in llms.read_text(encoding="utf-8"):
        raise AssemblyError(
            f"{channel} channel llms.txt does not declare {marker!r}"
        )

    for required in ("index.html", "index.md", "provenance.html", "provenance.md"):
        if not (channel_root / required).is_file():
            raise AssemblyError(f"{channel} channel is missing {required}")

    provenance = (channel_root / "provenance.html").read_text(encoding="utf-8")
    if channel not in provenance:
        raise AssemblyError(
            f"{channel} channel provenance does not name the channel {channel!r}"
        )

    for rel in _canonical_pages(channel_root):
        markdown = (channel_root / rel).with_suffix(".md")
        if not markdown.is_file() or not markdown.read_text(encoding="utf-8").strip():
            raise AssemblyError(
                f"{channel} channel is missing a Markdown alternative for "
                f"{rel.as_posix()}"
            )

    _validate_llms_links(channel_root, channel)


def _copy_channel(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, dirs_exist_ok=True)


def validate_aggregate(outdir: Path) -> None:
    """Fail loudly unless the combined artifact contains both channels."""

    _assert_no_forbidden_paths(outdir, "combined artifact")

    stable_root = outdir
    development_root = outdir / DEVELOPMENT_PREFIX

    if not (stable_root / "llms.txt").is_file():
        raise AssemblyError("combined artifact is missing the stable llms.txt")
    if not (stable_root / "index.html").is_file():
        raise AssemblyError("combined artifact is missing the stable index.html")
    if not development_root.is_dir():
        raise AssemblyError("combined artifact is missing the /dev/ channel")
    if not (development_root / "llms.txt").is_file():
        raise AssemblyError("combined artifact is missing /dev/llms.txt")
    if not (development_root / "index.html").is_file():
        raise AssemblyError("combined artifact is missing /dev/index.html")

    _validate_llms_links(stable_root, STABLE_CHANNEL)
    _validate_llms_links(development_root, DEVELOPMENT_CHANNEL)


def assemble(
    stable_dir: Path,
    development_dir: Path,
    outdir: Path,
    *,
    stable_channel: str = STABLE_CHANNEL,
    development_channel: str = DEVELOPMENT_CHANNEL,
) -> Path:
    """Build one fresh aggregate containing both channels.

    The inputs are validated before the output is touched, so a broken build
    cannot destroy a previously good artifact. The output is then recreated
    from scratch, which guarantees the result always contains exactly the
    stable channel at the root and the development channel under ``/dev/``.
    """

    stable_dir = Path(stable_dir)
    development_dir = Path(development_dir)
    outdir = Path(outdir)

    validate_channel(stable_dir, stable_channel)
    validate_channel(development_dir, development_channel)

    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True)

    _copy_channel(stable_dir, outdir)
    _copy_channel(development_dir, outdir / DEVELOPMENT_PREFIX)

    validate_aggregate(outdir)
    return outdir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stable", type=Path, required=True, help="built stable channel HTML dir"
    )
    parser.add_argument(
        "--development",
        type=Path,
        required=True,
        help="built development channel HTML dir",
    )
    parser.add_argument(
        "--outdir", type=Path, required=True, help="fresh aggregate output dir"
    )
    parser.add_argument(
        "--stable-channel",
        default=STABLE_CHANNEL,
        help=f"stable channel name (default: {STABLE_CHANNEL})",
    )
    parser.add_argument(
        "--development-channel",
        default=DEVELOPMENT_CHANNEL,
        help=f"development channel name (default: {DEVELOPMENT_CHANNEL})",
    )
    args = parser.parse_args(argv)
    try:
        outdir = assemble(
            args.stable,
            args.development,
            args.outdir,
            stable_channel=args.stable_channel,
            development_channel=args.development_channel,
        )
    except AssemblyError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Assembled two-channel site into {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
