"""Sphinx configuration for the public PyGV documentation site.

One documentation branch publishes exactly one channel. The channel's
``code-ref.json`` manifest names the public code commit that the rendered
signatures, defaults, and gallery examples must come from. The build entry
point (``tools/build_docs.py``) resolves that commit and communicates it to
this configuration through environment variables so that the build is
reproducible and never floats to a branch head.
"""

import json
import os
import shutil
from datetime import date
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent
REPO_ROOT = DOCS_DIR.parent


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default) or default


def _short(commit: str) -> str:
    return commit[:7] if commit and commit != "unknown" else commit


# -- Paired code reference ---------------------------------------------------

_manifest_path = REPO_ROOT / "code-ref.json"
_manifest = {}
if _manifest_path.is_file():
    _manifest = json.loads(_manifest_path.read_text(encoding="utf-8"))

DOC_CHANNEL = _env("PYGV_DOC_CHANNEL", _manifest.get("channel", "development"))
CODE_COMMIT = _env("PYGV_CODE_COMMIT", _manifest.get("commit", "unknown"))
CODE_BRANCH = _env("PYGV_CODE_BRANCH", _manifest.get("branch", "unknown"))
DOC_COMMIT = _env("PYGV_DOC_COMMIT", "unknown")

# The exact paired code checkout wins over any installed distribution so that
# autodoc and the gallery describe the manifest commit, not a release.
_code_dir = _env("PYGV_CODE_DIR")
if _code_dir and Path(_code_dir).is_dir():
    import sys

    sys.path.insert(0, _code_dir)


def _package_release() -> str:
    try:
        from pygv import __version__

        if __version__ and __version__ != "0.0.0":
            return __version__
    except Exception:
        pass
    try:
        from importlib.metadata import version as pkg_version

        return pkg_version("GenomeViewer")
    except Exception:
        return "0.0.0"


# -- Project information -----------------------------------------------------

project = "PyGV"
author = "Li Yao"
copyright = f"2021-{date.today().year}, Li Yao"
release = _package_release()
version = release

# -- General configuration ---------------------------------------------------

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
]

_source_suffix = {".md": "markdown", ".rst": "restructuredtext"}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
root_doc = "index"

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    "tasklist",
    "substitution",
    "attrs_block",
]
myst_heading_anchors = 3
myst_substitutions = {
    "doc_channel": DOC_CHANNEL,
    "doc_commit": DOC_COMMIT,
    "doc_commit_short": _short(DOC_COMMIT),
    "code_branch": CODE_BRANCH,
    "code_commit": CODE_COMMIT,
    "code_commit_short": _short(CODE_COMMIT),
    "release": release,
}

# -- Autodoc / autosummary ---------------------------------------------------

autosummary_generate = True
autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
    "undoc-members": False,
    "special-members": False,
    "inherited-members": False,
}
autodoc_typehints = "signature"
autodoc_member_order = "groupwise"
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_use_rtype = False

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "matplotlib": ("https://matplotlib.org/stable", None),
    "pydantic": ("https://docs.pydantic.dev/latest", None),
    "pandas": ("https://pandas.pydata.org/docs", None),
}

# -- Gallery -----------------------------------------------------------------

_code_examples = Path(_code_dir) / "examples" if _code_dir else None
if _code_examples and _code_examples.is_dir():
    extensions.append("sphinx_gallery.gen_gallery")
    _gallery_conf = {
        "examples_dirs": str(_code_examples),
        "gallery_dirs": "gallery",
        "filename_pattern": r"/plot_",
        "image_scrapers": ("matplotlib",),
        "within_subsection_order": "FileNameSortKey",
        "download_all_examples": True,
        "remove_config_comments": True,
        "compress_images": ("images", "thumbnails") if shutil.which("optipng") else (),
        "matplotlib_animations": False,
        "show_memory": False,
    }
    sphinx_gallery_conf = _gallery_conf

# -- HTML output -------------------------------------------------------------

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]
html_theme_options = {
    "show_nav_level": 3,
    "navigation_with_keys": True,
    "logo": {"text": f"{project} {release}"},
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/liyao001/PyGV",
            "icon": "fa-brands fa-github",
        },
    ],
    "use_edit_page_button": False,
    "footer_start": ["copyright"],
    "footer_end": ["last-updated"],
}
html_context = {
    "doc_channel": DOC_CHANNEL,
    "doc_commit": DOC_COMMIT,
    "doc_commit_short": _short(DOC_COMMIT),
    "code_branch": CODE_BRANCH,
    "code_commit": CODE_COMMIT,
    "code_commit_short": _short(CODE_COMMIT),
}
