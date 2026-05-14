import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services import workspace_tools
from app.services.workspace_tools import _resolve_project_dockerfile


class DummyResult:
    def __init__(self, values=None):
        self._values = list(values or [])

    def scalar_one_or_none(self):
        return self._values[0] if self._values else None

    def scalars(self):
        return self

    def all(self):
        return list(self._values)


class RecordingDB:
    def __init__(self, responses=None):
        self.responses = list(responses or [])
        self.statements = []
        self.commits = 0

    async def execute(self, statement):
        self.statements.append(str(statement))
        return self.responses.pop(0) if self.responses else DummyResult()

    async def commit(self):
        self.commits += 1


class SessionCtx:
    def __init__(self, db):
        self.db = db

    async def __aenter__(self):
        return self.db

    async def __aexit__(self, exc_type, exc, tb):
        return False


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


@pytest.mark.asyncio
async def test_list_workspace_projects_is_tenant_scoped(monkeypatch):
    tenant_id = uuid.uuid4()
    project = SimpleNamespace(slug="demo", name="Demo", status="deployed", deploy_type="static")
    db = RecordingDB([DummyResult([project])])

    monkeypatch.setattr(workspace_tools, "_get_agent_tenant_id", AsyncMock(return_value=tenant_id))
    monkeypatch.setattr(workspace_tools, "async_session", lambda: SessionCtx(db))

    result = await workspace_tools.tool_list_workspace_projects(uuid.uuid4())

    assert "workspace_projects.tenant_id =" in db.statements[0]
    assert "[demo]" in result


@pytest.mark.asyncio
async def test_resolve_bug_is_tenant_scoped(monkeypatch):
    tenant_id = uuid.uuid4()
    bug_id = uuid.uuid4()
    report = SimpleNamespace(id=bug_id, status="open")
    db = RecordingDB([DummyResult([report])])

    monkeypatch.setattr(workspace_tools, "_get_agent_tenant_id", AsyncMock(return_value=tenant_id))
    monkeypatch.setattr(workspace_tools, "async_session", lambda: SessionCtx(db))

    result = await workspace_tools.tool_resolve_bug({"bug_report_id": str(bug_id)}, uuid.uuid4())

    assert "workspace_projects.tenant_id =" in db.statements[0]
    assert report.status == "fixed"
    assert db.commits == 1
    assert "marked as fixed" in result

