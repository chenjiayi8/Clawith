import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api import workspace as workspace_api


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

    async def execute(self, statement):
        self.statements.append(str(statement))
        return self.responses.pop(0) if self.responses else DummyResult()


@pytest.mark.asyncio
async def test_list_projects_org_admin_is_tenant_scoped():
    tenant_id = uuid.uuid4()
    current_user = SimpleNamespace(role="org_admin", tenant_id=tenant_id, identity=None)
    db = RecordingDB([DummyResult([])])

    await workspace_api.list_projects(current_user=current_user, db=db)

    assert "workspace_projects.tenant_id =" in db.statements[0]


@pytest.mark.asyncio
async def test_list_projects_platform_admin_is_not_tenant_scoped():
    current_user = SimpleNamespace(role="platform_admin", tenant_id=uuid.uuid4(), identity=None)
    db = RecordingDB([DummyResult([])])

    await workspace_api.list_projects(current_user=current_user, db=db)

    assert "workspace_projects.tenant_id =" not in db.statements[0]


@pytest.mark.asyncio
async def test_approve_deploy_passes_tenant_scope_for_org_admin(monkeypatch):
    tenant_id = uuid.uuid4()
    current_user = SimpleNamespace(role="org_admin", tenant_id=tenant_id, identity=None)
    mock_approve = AsyncMock(return_value={"ok": True})
    monkeypatch.setattr(workspace_api, "approve_container_deploy", mock_approve)

    await workspace_api.approve_deploy(
        slug="demo",
        body=workspace_api.ApproveRequest(memory="256m"),
        current_user=current_user,
    )

    mock_approve.assert_awaited_once_with(
        "demo",
        {"memory": "256m"},
        tenant_id=tenant_id,
        include_platform_global=False,
    )


@pytest.mark.asyncio
async def test_reject_deploy_passes_global_scope_for_platform_admin(monkeypatch):
    current_user = SimpleNamespace(
        role="platform_admin",
        tenant_id=uuid.uuid4(),
        identity=SimpleNamespace(is_platform_admin=True),
    )
    mock_reject = AsyncMock(return_value={"ok": True})
    monkeypatch.setattr(workspace_api, "reject_container_deploy", mock_reject)

    await workspace_api.reject_deploy(slug="demo", current_user=current_user)

    mock_reject.assert_awaited_once_with(
        "demo",
        tenant_id=None,
        include_platform_global=True,
    )
