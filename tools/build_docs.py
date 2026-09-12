#!/usr/bin/env python3
"""Build one channel of the PyGV documentation site.

The documentation branch is paired with an exact public code commit through
``code-ref.json``. This entry point resolves that commit, validates that it
belongs to the named code branch, installs it, and then runs Sphinx with
warnings treated as errors.

Typical local use (offline, against an existing checkout)::

    python tools/build_docs.py --code-dir ../code

CI use (clone the pinned commit from the manifest)::

    python tools/build_docs.py --channel development --outdir build/html
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs"
MANIFEST_PATH = REPO_ROOT / "code-ref.json"
BUILD_ROOT = REPO_ROOT / ".build"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def run(cmd: list[str], *, cwd: Path | None = None, env: dict | None = None) -> None:
    print("+", " ".join(str(part) for part in cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def git(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )


def load_manifest() -> dict:
    if not MANIFEST_PATH.is_file():
        raise SystemExit(f"missing manifest: {MANIFEST_PATH}")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    missing = {"repository", "branch", "commit", "channel"} - manifest.keys()
    if missing:
        raise SystemExit(f"code-ref.json is missing keys: {sorted(missing)}")
    if not SHA_RE.match(manifest["commit"]):
        raise SystemExit("code-ref.json commit must be a full 40-character SHA")
    return manifest


def verify_commit(code_dir: Path, manifest: dict) -> None:
    commit = manifest["commit"]
    branch = manifest["branch"]

    if git("cat-file", "-e", f"{commit}^{{commit}}", cwd=code_dir).returncode != 0:
        raise SystemExit(f"commit {commit} is not present in {code_dir}")

    remotes = ["origin"] if git("remote", "get-url", "origin", cwd=code_dir).returncode == 0 else []
    contained = False
    for remote in remotes + [""]:
        ref = f"{remote}/{branch}" if remote else branch
        result = git("rev-parse", "--verify", "--quiet", ref, cwd=code_dir)
        if result.returncode != 0:
            continue
        if git("merge-base", "--is-ancestor", commit, ref, cwd=code_dir).returncode == 0:
            contained = True
            break
    if not contained:
        raise SystemExit(
            f"commit {commit} does not belong to code branch {branch!r}"
        )


def resolve_code_dir(manifest: dict, code_dir: Path | None) -> Path:
    if code_dir is not None:
        resolved = code_dir.resolve()
        if not (resolved / ".git").exists():
            raise SystemExit(f"--code-dir is not a git checkout: {resolved}")
        verify_commit(resolved, manifest)
        head = git("rev-parse", "HEAD", cwd=resolved).stdout.strip()
        if head != manifest["commit"]:
            print(
                f"warning: {resolved} HEAD is {head[:12]}, manifest is "
                f"{manifest['commit'][:12]}; the build imports the checkout as-is",
                file=sys.stderr,
            )
        return resolved

    dest = BUILD_ROOT / "code"
    if not (dest / ".git").exists():
        BUILD_ROOT.mkdir(parents=True, exist_ok=True)
        run(
            [
                "git",
                "clone",
                "--filter=blob:none",
                "--no-checkout",
                manifest["repository"],
                str(dest),
            ]
        )
    run(["git", "fetch", "--depth", "1", "origin", manifest["commit"]], cwd=dest)
    run(["git", "checkout", "--force", manifest["commit"]], cwd=dest)
    verify_commit(dest, manifest)
    return dest


def install_code(code_dir: Path, enabled: bool) -> None:
    if not enabled:
        return
    run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--editable",
            str(code_dir),
        ]
    )


def doc_commit() -> str:
    if not (REPO_ROOT / ".git").exists():
        return "unknown"
    result = git("rev-parse", "HEAD", cwd=REPO_ROOT)
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def dependency_lock_digest() -> str:
    """Short digest of the documentation dependency lock.

    The gallery cache identity must change whenever the pins in
    ``requirements.txt`` change, because a different Matplotlib or
    Sphinx-Gallery version can render a different figure.
    """
    lock = REPO_ROOT / "requirements.txt"
    if not lock.is_file():
        return "nolock"
    return hashlib.sha256(lock.read_bytes()).hexdigest()[:12]


def gallery_dir(channel: str, commit: str, lock_digest: str) -> str:
    """Relative (to ``docs/``) gallery output path for one build identity.

    The path folds in the channel, the exact paired code revision, and the
    dependency lock digest, so generated gallery pages from a different build
    identity can never be reused or picked up by the glob toctree.
    """
    return f"gallery/{channel}/{commit[:12]}-{lock_digest}"


def prune_gallery(target: str) -> None:
    """Delete generated galleries that do not belong to this build.

    Gallery sources are disposable and revision-keyed. Removing sibling
    revisions and other channels keeps a stale glob toctree from publishing
    generated pages that no longer match the paired checkout.
    """
    root = DOCS_DIR / "gallery"
    if not root.is_dir():
        return
    keep = (DOCS_DIR / target).resolve()
    for channel_dir in root.iterdir():
        if not channel_dir.is_dir():
            continue
        if channel_dir.resolve() != keep.parent:
            shutil.rmtree(channel_dir, ignore_errors=True)
            continue
        for revision_dir in channel_dir.iterdir():
            if revision_dir.is_dir() and revision_dir.resolve() != keep:
                shutil.rmtree(revision_dir, ignore_errors=True)


def build(args: argparse.Namespace) -> Path:
    manifest = load_manifest()
    channel = args.channel or manifest["channel"]
    code_dir = resolve_code_dir(manifest, args.code_dir)
    install_code(code_dir, enabled=not args.no_install)

    outdir = (args.outdir or (REPO_ROOT / "build" / "html")).resolve()
    doctrees = outdir.parent / "doctrees"
    outdir.mkdir(parents=True, exist_ok=True)

    gallery = gallery_dir(channel, manifest["commit"], dependency_lock_digest())
    prune_gallery(gallery)

    env = os.environ.copy()
    env.update(
        {
            "PYGV_CODE_DIR": str(code_dir),
            "PYGV_CODE_COMMIT": manifest["commit"],
            "PYGV_CODE_BRANCH": manifest["branch"],
            "PYGV_DOC_CHANNEL": channel,
            "PYGV_DOC_COMMIT": doc_commit(),
            "PYGV_GALLERY_DIR": gallery,
        }
    )

    cmd = [
        sys.executable,
        "-m",
        "sphinx",
        "-b",
        args.builder,
        "-W",
        "--keep-going",
        "-d",
        str(doctrees),
        str(DOCS_DIR),
        str(outdir),
    ]
    run(cmd, env=env)
    return outdir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", help="channel name; defaults to the manifest")
    parser.add_argument(
        "--code-dir",
        type=Path,
        help="existing code checkout to import instead of cloning the manifest commit",
    )
    parser.add_argument(
        "--outdir", type=Path, help="output directory (default: build/html)"
    )
    parser.add_argument("--builder", default="html", help="Sphinx builder (default: html)")
    parser.add_argument(
        "--no-install",
        action="store_true",
        help="do not pip-install the resolved code checkout",
    )
    args = parser.parse_args(argv)
    outdir = build(args)
    print(f"Built documentation into {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
