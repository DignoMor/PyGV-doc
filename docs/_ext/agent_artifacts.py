"""Publish agent-readable artifacts beside the built HTML site.

A coding agent that fetches the documentation site should not have to parse
theme chrome, and it must never see the *source* directives (``{autoclass}``,
``.. autofunction::``) that the build resolves. This extension therefore runs
after an HTML build and, for every canonical human-facing page:

* writes a processed Markdown alternative next to the page, converted from the
  rendered article so it carries the expanded signatures, fields, and
  docstrings;
* writes one curated ``llms.txt`` at the channel output root that groups and
  describes the canonical resources; and
* injects discovery metadata into the page ``<head>`` advertising both the
  Markdown alternate and the channel-scoped ``llms.txt``.

All URLs are relative, so the same artifact is correct at the Pages project
root and beneath the ``/dev/`` development subtree. No ``llms-full.txt`` is
produced, and private planning material never enters the artifact because only
rendered public pages are converted.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

# Pages that are navigation/search plumbing rather than canonical content.
_EXCLUDED_NAMES = {
    "search.html",
    "genindex.html",
    "py-modindex.html",
    "modindex.html",
    "404.html",
}
_EXCLUDED_PARTS = {"_static", "_sources", "_downloads", "_images"}

_INLINE_TAGS = {
    "em",
    "i",
    "cite",
    "var",
    "strong",
    "b",
    "code",
    "tt",
    "kbd",
    "samp",
    "a",
    "span",
    "img",
    "sup",
    "sub",
    "abbr",
    "q",
    "small",
    "u",
    "s",
    "del",
    "ins",
    "mark",
    "br",
}


def _is_excluded(rel: Path) -> bool:
    if rel.name in _EXCLUDED_NAMES:
        return True
    return any(part in _EXCLUDED_PARTS for part in rel.parts)


def _collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


class _MarkdownConverter:
    """Convert a rendered Sphinx article to Markdown.

    The converter deliberately ignores presentation wrappers and keeps the
    semantic structures that carry API meaning: headings, definition lists
    (autodoc signatures and configuration fields), code blocks, tables, and
    admonitions.
    """

    def convert(self, article: Tag) -> str:
        for anchor in article.find_all("a", class_="headerlink"):
            anchor.decompose()
        text = self._blocks(article)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip() + "\n"

    # -- block level -------------------------------------------------------

    def _blocks(self, node: Tag) -> str:
        parts: list[str] = []
        buffer: list[str] = []

        def flush() -> None:
            text = _collapse("".join(buffer))
            if text:
                parts.append(text)
            buffer.clear()

        for child in node.children:
            if isinstance(child, NavigableString):
                buffer.append(str(child))
            elif not isinstance(child, Tag):
                continue
            elif child.name in _INLINE_TAGS:
                buffer.append(self._inline(child))
            elif child.name in {"script", "style", "form"}:
                continue
            else:
                flush()
                rendered = self._block(child)
                if rendered and rendered.strip():
                    parts.append(rendered.strip("\n"))

        flush()
        return "\n\n".join(part for part in parts if part.strip())

    def _block(self, node: Tag) -> str:
        name = node.name
        if re.fullmatch(r"h[1-6]", name):
            level = int(name[1])
            title = _collapse(self._inline_children(node))
            return f"{'#' * level} {title}".rstrip()
        if name == "p":
            return self._inline_children(node).strip()
        if name == "pre":
            code = "".join(node.strings).strip("\n")
            return f"```\n{code}\n```"
        if name in {"ul", "ol"}:
            return self._list(node)
        if name == "dl":
            return self._dl(node)
        if name == "table":
            return self._table(node)
        if name == "blockquote":
            inner = self._blocks(node)
            return self._quote(inner)
        if name == "hr":
            return "---"
        if name == "figcaption":
            return _collapse(self._inline_children(node))
        if name == "div":
            classes = set(node.get("class") or [])
            if "admonition" in classes:
                return self._admonition(node)
            if "highlight" in classes or any(
                cls.startswith("highlight-") for cls in classes
            ):
                pre = node.find("pre")
                if pre is not None:
                    return self._block(pre)
            return self._blocks(node)
        if name in {"section", "figure", "details", "article"}:
            return self._blocks(node)
        return self._blocks(node)

    def _list(self, node: Tag) -> str:
        ordered = node.name == "ol"
        items: list[str] = []
        for index, li in enumerate(node.find_all("li", recursive=False), start=1):
            marker = f"{index}." if ordered else "-"
            inline: list[str] = []
            nested: list[str] = []
            for child in li.children:
                if isinstance(child, Tag) and child.name in {"ul", "ol"}:
                    nested.append(self._list(child))
                elif isinstance(child, NavigableString):
                    inline.append(str(child))
                elif isinstance(child, Tag) and child.name in _INLINE_TAGS:
                    inline.append(self._inline(child))
                elif isinstance(child, Tag):
                    inline.append(self._blocks(child))
            text = _collapse("".join(inline))
            item = f"{marker} {text}".rstrip()
            for sub in nested:
                item += "\n" + "\n".join("  " + line for line in sub.splitlines())
            items.append(item)
        return "\n".join(items)

    def _dl(self, node: Tag) -> str:
        classes = set(node.get("class") or [])
        is_signature = "sig" in classes or "sig-object" in classes
        blocks: list[str] = []
        children = [child for child in node.children if isinstance(child, Tag)]
        index = 0
        while index < len(children):
            dt = children[index]
            if dt.name != "dt":
                index += 1
                continue
            definitions: list[Tag] = []
            cursor = index + 1
            while cursor < len(children) and children[cursor].name == "dd":
                definitions.append(children[cursor])
                cursor += 1

            if is_signature or "sig-object" in set(dt.get("class") or []):
                signature = _collapse("".join(dt.strings)).rstrip("#").strip()
                pieces = [f"```\n{signature}\n```"] if signature else []
            else:
                term = _collapse(self._inline_children(dt))
                pieces = [f"**{term}**"] if term else []

            for definition in definitions:
                interior = self._blocks(definition).strip()
                if interior:
                    pieces.append(interior)
            joined = "\n\n".join(piece for piece in pieces if piece.strip())
            if joined.strip():
                blocks.append(joined)
            index = cursor
        return "\n\n".join(blocks)

    def _table(self, node: Tag) -> str:
        rows: list[list[str]] = []
        for row in node.find_all("tr"):
            cells = [
                _collapse(self._inline_children(cell)).replace("|", "\\|")
                for cell in row.find_all(["th", "td"])
            ]
            if cells:
                rows.append(cells)
        if not rows:
            return ""
        width = max(len(row) for row in rows)
        rows = [row + [""] * (width - len(row)) for row in rows]
        lines = [
            "| " + " | ".join(rows[0]) + " |",
            "| " + " | ".join(["---"] * width) + " |",
        ]
        lines.extend("| " + " | ".join(row) + " |" for row in rows[1:])
        return "\n".join(lines)

    def _admonition(self, node: Tag) -> str:
        title = node.find(class_="admonition-title")
        title_text = ""
        if title is not None:
            title_text = _collapse(title.get_text(" "))
            title.decompose()
        body = self._blocks(node)
        lines: list[str] = []
        if title_text:
            lines.append(f"**{title_text}**")
        lines.extend(body.splitlines())
        return self._quote("\n".join(lines))

    @staticmethod
    def _quote(text: str) -> str:
        return "\n".join(
            f"> {line}" if line.strip() else ">" for line in text.splitlines()
        )

    # -- inline level ------------------------------------------------------

    def _inline_children(self, node: Tag) -> str:
        return "".join(self._inline(child) for child in node.children)

    def _inline(self, node: object) -> str:
        if isinstance(node, NavigableString):
            return str(node)
        if not isinstance(node, Tag):
            return ""
        name = node.name
        if name in {"script", "style"}:
            return ""
        if name in {"em", "i", "cite", "var"}:
            inner = self._inline_children(node)
            return f"*{inner}*" if inner.strip() else ""
        if name in {"strong", "b"}:
            inner = self._inline_children(node)
            return f"**{inner}**" if inner.strip() else ""
        if name in {"code", "tt", "kbd", "samp"}:
            inner = "".join(node.strings).strip()
            return f"`{inner}`" if inner else ""
        if name in {"s", "del"}:
            inner = self._inline_children(node)
            return f"~~{inner}~~" if inner.strip() else ""
        if name == "a":
            if "headerlink" in set(node.get("class") or []):
                return ""
            href = node.get("href", "")
            inner = _collapse(self._inline_children(node))
            if not href:
                return inner
            return f"[{inner or href}]({href})"
        if name == "img":
            src = node.get("src", "")
            alt = node.get("alt", "") or ""
            return f"![{alt}]({src})" if src else alt
        if name == "br":
            return "\n"
        if name in {"sup", "sub"}:
            return self._inline_children(node)
        return self._inline_children(node)


def _convert_html(raw: str) -> str:
    soup = BeautifulSoup(raw, "html.parser")
    article = soup.find("article")
    if article is None:
        main = soup.find("main")
        article = main if main is not None else soup.body
    if article is None:
        return ""
    return _MarkdownConverter().convert(article)


def _canonical_pages(outdir: Path) -> list[Path]:
    pages: list[Path] = []
    for path in sorted(outdir.rglob("*.html")):
        rel = path.relative_to(outdir)
        if _is_excluded(rel):
            continue
        pages.append(rel)
    return pages


# -- Channel context ---------------------------------------------------------


def _manifest(app) -> dict:
    path = Path(app.confdir).parent / "code-ref.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _context(app) -> dict:
    manifest = _manifest(app)

    def env(name: str, fallback: str) -> str:
        return os.environ.get(name) or fallback

    return {
        "channel": env("PYGV_DOC_CHANNEL", manifest.get("channel", "unknown")),
        "code_commit": env("PYGV_CODE_COMMIT", manifest.get("commit", "unknown")),
        "code_branch": env("PYGV_CODE_BRANCH", manifest.get("branch", "unknown")),
        "doc_commit": env("PYGV_DOC_COMMIT", "unknown"),
        "version": getattr(app.config, "release", "unknown"),
    }


def _short(commit: str) -> str:
    return commit[:7] if commit and commit != "unknown" else commit


def _llms_txt(app, outdir: Path) -> str:
    ctx = _context(app)
    lines: list[str] = []
    lines.append("# PyGV")
    lines.append("")
    lines.append(
        "> PyGV (the Python Genome Viewer) builds publication-ready genome "
        "browser figures as ordinary Matplotlib figures. Compose a genome "
        "viewer from typed track objects over one genomic interval and render, "
        "inspect, or save it."
    )
    lines.append("")
    lines.append(
        f"- Documentation channel: {ctx['channel']}; describes GenomeViewer "
        f"{ctx['version']} at code commit {_short(ctx['code_commit'])} "
        f"({ctx['code_branch']} branch)."
    )
    lines.append(
        "- Install with `pip install GenomeViewer`; import the package as "
        "`pygv` (for example `from pygv.viewer import GenomeViewer`)."
    )
    lines.append(
        "- Genomic coordinates are zero-based and half-open: an interval "
        "`(start, end)` includes `start` and excludes `end`."
    )
    lines.append(
        "- Every page below also has a `.md` alternate at the same path with "
        "expanded signatures, fields, and docstrings."
    )
    lines.append("")

    lines.append("## Start here")
    lines.append("")
    lines.append(
        "- [Documentation index](index.md): entry point and navigation for the "
        "whole channel."
    )
    lines.append(
        "- [Overview](overview.md): what PyGV does, the distribution vs import "
        "names, and the canonical glossary."
    )
    lines.append(
        "- [Installation and quickstart](installation.md): install, import, and "
        "a runnable first figure."
    )
    lines.append(
        "- [Core concepts](concepts.md): viewers, tracks, sources, intervals, "
        "layout, rendering, annotations, and autoscale."
    )
    lines.append(
        "- [Track guide](track-guide.md): choose a track by genomic data type, "
        "with a per-family API map."
    )
    lines.append(
        "- [Data formats and coordinates](data-formats.md): supported sources, "
        "local vs remote inputs, indexing, and validation."
    )
    lines.append("")

    lines.append("## API reference")
    lines.append("")
    lines.append(
        "- [API reference index](api/index.md): how the generated reference is "
        "organized and pinned."
    )
    lines.append(
        "- [GenomeViewer](api/viewer.md): constructor plus track registration, "
        "layout, shared annotations, rendering, and saving."
    )
    lines.append(
        "- [Track API reference](api/tracks.md): every class exported by "
        "`pygv.tracks`, including inherited configuration fields, defaults, "
        "literals, and compatibility aliases."
    )
    lines.append(
        "- [Utilities](api/utilities.md): public helper functions such as "
        "`check_accessibility`."
    )
    lines.append("")

    gallery_indexes = sorted(outdir.glob("gallery/*/*/index.md"))
    examples = sorted(outdir.glob("gallery/*/*/plot_*.md"))
    lines.append("## Examples")
    lines.append("")
    lines.append(
        "- [Complete gallery](gallery.md): how examples are executed and "
        "rendered from the pinned checkout."
    )
    for gallery_index in gallery_indexes:
        rel = gallery_index.relative_to(outdir).as_posix()
        lines.append(
            f"- [Generated example gallery]({rel}): one rendered, executed page "
            "per public example."
        )
    if examples:
        listed = ", ".join(
            f"[{example.stem}]({example.relative_to(outdir).as_posix()})"
            for example in examples[:4]
        )
        lines.append(
            f"- Representative examples: {listed}, and more in the generated "
            "gallery index."
        )
    lines.append("")

    lines.append("## Project metadata")
    lines.append("")
    lines.append(
        "- [Changelog and migration](changelog.md): compatibility changes and a "
        "migration checklist for this revision."
    )
    lines.append(
        "- [Build provenance](provenance.md): the exact documentation and code "
        "revisions this channel describes."
    )
    lines.append(
        "- [Third-party notices](third-party-notices.md): licenses and terms for "
        "bundled example data and assets."
    )
    lines.append("")
    return "\n".join(lines)


# -- Discovery metadata ------------------------------------------------------


def _inject_discovery(outdir: Path, pages: list[Path]) -> None:
    marker = 'name="pygv-agent-artifacts"'
    for rel in pages:
        path = outdir / rel
        raw = path.read_text(encoding="utf-8")
        if marker in raw:
            continue
        markdown_href = rel.with_suffix(".md").name
        llms_href = os.path.relpath(outdir / "llms.txt", path.parent).replace(
            os.sep, "/"
        )
        snippet = (
            '<link rel="alternate" type="text/markdown" '
            f'href="{markdown_href}" title="Markdown alternate" />\n'
            '<link rel="llms" type="text/plain" '
            f'href="{llms_href}" title="llms.txt" />\n'
            '<link rel="describedby" type="text/plain" '
            f'href="{llms_href}" />\n'
            f'<meta name="pygv-agent-artifacts" content="markdown,llms.txt" />\n'
        )
        raw = raw.replace("</head>", snippet + "</head>", 1)
        path.write_text(raw, encoding="utf-8")


# -- Sphinx hook -------------------------------------------------------------


def _on_build_finished(app, exception) -> None:
    if exception is not None:
        return
    if getattr(app.builder, "format", None) != "html":
        return

    outdir = Path(app.outdir)
    pages = _canonical_pages(outdir)

    for rel in pages:
        raw = (outdir / rel).read_text(encoding="utf-8")
        markdown = _convert_html(raw)
        (outdir / rel.with_suffix(".md")).write_text(markdown, encoding="utf-8")

    (outdir / "llms.txt").write_text(_llms_txt(app, outdir), encoding="utf-8")
    _inject_discovery(outdir, pages)


def setup(app):
    app.connect("build-finished", _on_build_finished)
    return {"version": "1.0", "parallel_read_safe": True}
