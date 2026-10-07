"""Version provenance must work without an installed code distribution."""

import importlib.util
import subprocess
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools" / "build_docs.py"
spec = importlib.util.spec_from_file_location("build_docs", TOOLS)
build_docs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_docs)


@pytest.fixture
def checkout(tmp_path):
    def git(*args):
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)

    git("init")
    git("config", "user.name", "Docs Test")
    git("config", "user.email", "docs@example.invalid")
    (tmp_path / "pyproject.toml").write_text(
        '[tool.hatch.version]\nsource = "vcs"\nfallback-version = "0.0.0"\n'
        '[tool.hatch.version.raw-options]\nversion_scheme = "post-release"\n'
        'git_describe_command = "git describe --dirty --tags --long '
        '--match [0-9]* --match v[0-9]* --exclude *dev*"\n',
        encoding="utf-8",
    )
    git("add", ".")
    git("commit", "-m", "Initial checkout")
    return tmp_path, git


def test_clean_tagged_checkout_resolves_without_generated_version_file(checkout):
    path, git = checkout
    git("tag", "1.2.3")
    assert build_docs.code_release(path) == "1.2.3"
    assert not (path / "pygv" / "_version.py").exists()


def test_development_checkout_uses_package_post_release_scheme(checkout):
    path, git = checkout
    git("tag", "1.2.3")
    git("commit", "--allow-empty", "-m", "Development change")
    assert build_docs.code_release(path).startswith("1.2.3.post1+g")


def test_no_reachable_release_tag_fails_instead_of_falling_back(checkout):
    path, _ = checkout
    with pytest.raises(SystemExit, match="no reachable release tag"):
        build_docs.code_release(path)
