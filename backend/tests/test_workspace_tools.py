from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services.workspace_tools import _resolve_project_dockerfile


def test_resolve_project_dockerfile_prefers_stored_path(tmp_path: Path):
    agent_ws = tmp_path / "agent"
    primary = agent_ws / "workspace" / "my-app" / "Dockerfile"
    stray = agent_ws / "workspace" / "other" / "Dockerfile"
    primary.parent.mkdir(parents=True, exist_ok=True)
    stray.parent.mkdir(parents=True, exist_ok=True)
    primary.write_text("FROM python:3.12\n")
    stray.write_text("FROM node:20\n")

    project = SimpleNamespace(dockerfile_path="workspace/my-app/Dockerfile")

    resolved = _resolve_project_dockerfile(agent_ws, "demo", project)

    assert resolved == primary


def test_resolve_project_dockerfile_rejects_ambiguous_fallback(tmp_path: Path):
    agent_ws = tmp_path / "agent"
    first = agent_ws / "workspace" / "demo" / "api" / "Dockerfile"
    second = agent_ws / "workspace" / "demo" / "worker" / "Dockerfile"
    first.parent.mkdir(parents=True, exist_ok=True)
    second.parent.mkdir(parents=True, exist_ok=True)
    first.write_text("FROM python:3.12\n")
    second.write_text("FROM node:20\n")

    project = SimpleNamespace(dockerfile_path=None)

    with pytest.raises(ValueError, match="Multiple Dockerfiles found"):
        _resolve_project_dockerfile(agent_ws, "demo", project)
