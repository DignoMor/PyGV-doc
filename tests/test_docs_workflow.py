"""Static validation of ``.github/workflows/docs.yml``.

These tests never run the workflow and touch no external service. They pin the
security and shape of the two-channel Pages pipeline: triggers, the read-only
pull-request path, the write-scoped deploy path, concurrency, and the absence
of any custom domain or Read the Docs coupling.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "docs.yml"


# -- Minimal YAML fallback ---------------------------------------------------


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _scalar(text: str):
    text = text.strip()
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        return [] if not inner else [_scalar(part) for part in inner.split(",")]
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        return text[1:-1]
    lowered = text.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "~", ""}:
        return None
    return text


def _parse_block_scalar(lines, index, indent):
    collected = []
    while index < len(lines) and _indent(lines[index]) > indent:
        collected.append(lines[index])
        index += 1
    if not collected:
        return "", index
    strip = min(_indent(line) for line in collected)
    return "\n".join(line[strip:] for line in collected), index


def _is_map_fragment(content: str) -> bool:
    if content.startswith(("'", '"', "[", "{")):
        return False
    key, sep, _ = content.partition(":")
    return bool(sep and key.strip() and " " not in key.strip())


def _parse_node(lines, index, indent):
    if lines[index].strip().startswith("- "):
        return _parse_seq(lines, index, indent)
    return _parse_map(lines, index, indent)


def _parse_map(lines, index, indent):
    result = {}
    while (
        index < len(lines)
        and _indent(lines[index]) == indent
        and not lines[index].strip().startswith("- ")
    ):
        key, sep, rest = lines[index].strip().partition(":")
        if not sep:
            raise ValueError(f"expected a mapping entry: {lines[index]!r}")
        key, rest = key.strip(), rest.strip()
        index += 1
        if rest in {"|", ">"}:
            result[key], index = _parse_block_scalar(lines, index, indent)
        elif rest == "":
            if index < len(lines) and (
                _indent(lines[index]) > indent
                or lines[index].strip().startswith("- ")
            ):
                result[key], index = _parse_node(
                    lines, index, _indent(lines[index])
                )
            else:
                result[key] = None
        else:
            result[key] = _scalar(rest)
    return result, index


def _parse_seq(lines, index, indent):
    result = []
    while (
        index < len(lines)
        and _indent(lines[index]) == indent
        and lines[index].strip().startswith("- ")
    ):
        content = lines[index].strip()[2:]
        index += 1
        if content == "":
            if index < len(lines) and _indent(lines[index]) > indent:
                value, index = _parse_node(lines, index, _indent(lines[index]))
            else:
                value = None
            result.append(value)
        elif _is_map_fragment(content):
            item = {}
            key, _, rest = content.partition(":")
            key, rest = key.strip(), rest.strip()
            if rest:
                item[key] = _scalar(rest)
            elif index < len(lines) and _indent(lines[index]) > indent:
                item[key], index = _parse_node(lines, index, _indent(lines[index]))
            else:
                item[key] = None
            while index < len(lines) and _indent(lines[index]) > indent:
                extra, index = _parse_map(lines, index, _indent(lines[index]))
                item.update(extra)
            result.append(item)
        else:
            result.append(_scalar(content))
    return result, index


def _minimal_load(text: str):
    lines = []
    for raw in text.splitlines():
        stripped = raw.rstrip()
        if not stripped.strip() or stripped.lstrip().startswith("#"):
            continue
        lines.append(stripped)
    if not lines:
        return {}
    value, index = _parse_node(lines, 0, _indent(lines[0]))
    if index != len(lines):
        raise ValueError("minimal loader did not consume the whole document")
    return value


def _load_workflow():
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    try:
        import yaml
    except ImportError:
        return _minimal_load(text)
    return yaml.safe_load(text)


@pytest.fixture(scope="module")
def workflow():
    data = _load_workflow()
    assert isinstance(data, dict)
    return data


@pytest.fixture(scope="module")
def workflow_text():
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def _triggers(data):
    triggers = data.get("on")
    if triggers is None:
        triggers = data.get(True)
    assert triggers is not None, "workflow declares no on: triggers"
    return triggers


def _job(data, name):
    assert name in data["jobs"], f"workflow has no {name!r} job"
    return data["jobs"][name]


def _steps(job):
    return job.get("steps", [])


def _uses(job):
    return [step.get("uses", "") for step in _steps(job)]


def _runs(job):
    return "\n".join(step.get("run", "") for step in _steps(job))


# -- Triggers ----------------------------------------------------------------


def test_workflow_file_exists():
    assert WORKFLOW_PATH.is_file()


def test_push_triggers_both_documentation_channels(workflow):
    push = _triggers(workflow)["push"]
    branches = push["branches"]
    assert "main" in branches
    assert "dev" in branches


def test_triggers_workflow_dispatch_and_pull_request(workflow):
    triggers = _triggers(workflow)
    assert "workflow_dispatch" in triggers
    assert "pull_request" in triggers


# -- Pull-request path is read-only and never deploys ------------------------


def test_workflow_default_permissions_are_read_only(workflow):
    assert workflow["permissions"] == {"contents": "read"}


def test_build_job_permissions_are_read_only(workflow):
    permissions = _job(workflow, "build")["permissions"]
    assert permissions.get("contents") == "read"
    assert "pages" not in permissions
    assert "id-token" not in permissions
    assert "write" not in permissions.values()


def test_build_job_never_invokes_pages_deployment(workflow):
    uses = " ".join(_uses(_job(workflow, "build")))
    assert "actions/configure-pages" not in uses
    assert "actions/upload-pages-artifact" not in uses
    assert "actions/deploy-pages" not in uses


def test_build_job_uploads_an_inspectable_artifact(workflow):
    steps = _steps(_job(workflow, "build"))
    uploads = [
        step
        for step in steps
        if step.get("uses", "").startswith("actions/upload-artifact@")
    ]
    assert uploads, "build job does not upload an ordinary artifact"
    assert uploads[0]["with"]["name"] == "docs-site"
    assert uploads[0]["with"]["if-no-files-found"] == "error"


# -- Both channels run the same strict checks --------------------------------


def test_build_job_builds_both_channels_with_build_docs(workflow):
    runs = _runs(_job(workflow, "build"))
    assert runs.count("tools/build_docs.py") == 2
    assert "--channel stable" in runs
    assert "--channel development" in runs
    assert "--no-install" in runs


def test_build_job_runs_the_strict_suite_for_both_channels(workflow):
    runs = _runs(_job(workflow, "build"))
    assert runs.count("pytest") == 2
    assert "doc-main/tests" in runs
    assert "doc-dev/tests" in runs


def test_build_job_assembles_the_combined_artifact(workflow):
    runs = _runs(_job(workflow, "build"))
    assert "tools/assemble_site.py" in runs
    assert "--stable" in runs
    assert "--development" in runs
    assert "--outdir" in runs


# -- Deploy path is gated and minimally scoped -------------------------------


def test_deploy_job_is_gated_off_pull_requests(workflow):
    deploy = _job(workflow, "deploy")
    assert "pull_request" in deploy["if"]
    assert "!=" in deploy["if"]
    assert deploy.get("needs") == "build"


def test_deploy_job_has_only_pages_write_and_id_token(workflow):
    permissions = _job(workflow, "deploy")["permissions"]
    assert permissions == {"pages": "write", "id-token": "write"}


def test_deploy_job_uses_official_pages_actions(workflow):
    uses = " ".join(_uses(_job(workflow, "deploy")))
    assert "actions/upload-pages-artifact" in uses
    assert "actions/deploy-pages" in uses


def test_pages_write_is_confined_to_the_deploy_job(workflow):
    build_permissions = _job(workflow, "build")["permissions"]
    deploy_permissions = _job(workflow, "deploy")["permissions"]
    assert "pages" not in build_permissions
    assert deploy_permissions["pages"] == "write"


# -- Concurrency -------------------------------------------------------------


def test_concurrency_prevents_stale_replacements(workflow):
    concurrency = workflow.get("concurrency")
    assert concurrency, "workflow has no concurrency configuration"
    assert concurrency.get("group")
    assert concurrency.get("cancel-in-progress") is True

    deploy_concurrency = _job(workflow, "deploy").get("concurrency")
    assert deploy_concurrency, "deploy job has no concurrency configuration"
    assert deploy_concurrency.get("group")
    assert deploy_concurrency.get("cancel-in-progress") is True


# -- Forbidden configuration -------------------------------------------------


def test_no_custom_domain_or_cname(workflow_text):
    lowered = workflow_text.lower()
    assert "cname" not in lowered
    assert "custom domain" not in lowered
    assert "github-pages" in lowered  # the managed Pages environment only


def test_no_read_the_docs_coupling(workflow_text):
    lowered = workflow_text.lower()
    assert "readthedocs" not in lowered
    assert "read the docs" not in lowered
    assert not re.search(r"\brtd\b", lowered)
    assert "readthedocs.io" not in lowered


def test_minimal_fallback_loader_understands_the_workflow():
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    data = _minimal_load(text)
    assert set(data["jobs"]) == {"build", "deploy"}
    assert data["on"]["push"]["branches"] == ["main", "dev"]
    assert "pull_request" in data["on"]
    assert "workflow_dispatch" in data["on"]
    assert data["jobs"]["build"]["permissions"] == {"contents": "read"}
    assert data["jobs"]["deploy"]["permissions"] == {
        "pages": "write",
        "id-token": "write",
    }
    assert data["jobs"]["deploy"]["if"] == "github.event_name != 'pull_request'"
