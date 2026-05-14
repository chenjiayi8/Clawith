import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services import workspace_tools
from app.services.workspace_tools import _resolve_project_dockerfile


class RecordingSession:
    def __init__(self, execute_result=None):
        self.execute_result = execute_result
        self.added = []
        self.committed = False

    async def execute(self, _query):
        return self.execute_result

    def add(self, project):
        self.added.append(project)

    async def commit(self):
        self.committed = True


class SessionContext:
    def __init__(self, session: RecordingSession):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return False


class ScalarsResult:
    def __init__(self, values):
        self.values = values

    def scalars(self):
        return self

    def all(self):
        return self.values


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
async def test_tool_request_build_persists_agent_owned_request(monkeypatch):
    session = RecordingSession()
    agent_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    monkeypatch.setattr(workspace_tools, "async_session", lambda: SessionContext(session))
    monkeypatch.setattr(workspace_tools, "check_slug_available", AsyncMock(return_value=None))
    monkeypatch.setattr(workspace_tools, "_get_agent_tenant_id", AsyncMock(return_value=tenant_id))

    response = await workspace_tools.tool_request_build(
        agent_id,
        {"slug": "demo-app", "name": "Demo App", "description": "Tenant-aware build request"},
    )

    assert response == (
        "Build request created!\n"
        "- Slug: demo-app\n"
        "- Name: Demo App\n"
        "- Description: Tenant-aware build request\n"
        "The Software Engineer agent will pick this up."
    )
    assert session.committed is True
    assert len(session.added) == 1
    project = session.added[0]
    assert project.slug == "demo-app"
    assert project.name == "Demo App"
    assert project.description == "Tenant-aware build request"
    assert project.tenant_id == tenant_id
    assert project.requested_by == agent_id
    assert project.status == "requested"


@pytest.mark.asyncio
async def test_tool_request_build_human_defaults_requester(monkeypatch):
    session = RecordingSession()
    monkeypatch.setattr(workspace_tools, "async_session", lambda: SessionContext(session))
    monkeypatch.setattr(workspace_tools, "check_slug_available", AsyncMock(return_value=None))

    response = await workspace_tools.tool_request_build_human(
        {"slug": "demo-app", "name": "Demo App", "description": "Human request", "requester": "   "}
    )

    assert response == "Build request 'Demo App' created for slug 'demo-app'."
    assert session.committed is True
    assert len(session.added) == 1
    project = session.added[0]
    assert project.slug == "demo-app"
    assert project.name == "Demo App"
    assert project.description == "Human request"
    assert project.requested_by_human == "Frank"
    assert project.status == "requested"


@pytest.mark.asyncio
async def test_tool_list_build_requests_formats_human_and_agent_requesters(monkeypatch):
    agent_id = uuid.uuid4()
    session = RecordingSession(
        ScalarsResult(
            [
                SimpleNamespace(
                    slug="human-app",
                    name="Human App",
                    description="Requested from dashboard",
                    requested_by_human="Avery",
                    requested_by=None,
                ),
                SimpleNamespace(
                    slug="agent-app",
                    name="Agent App",
                    description="Requested from agent",
                    requested_by_human=None,
                    requested_by=agent_id,
                ),
            ]
        )
    )
    monkeypatch.setattr(workspace_tools, "async_session", lambda: SessionContext(session))

    response = await workspace_tools.tool_list_build_requests()

    assert response == (
        "Pending build requests:\n\n"
        "- [human-app] Human App\n"
        "  Requested by: Avery\n"
        "  Description: Requested from dashboard\n\n"
        f"- [agent-app] Agent App\n"
        f"  Requested by: Agent {agent_id}\n"
        "  Description: Requested from agent\n"
    )
