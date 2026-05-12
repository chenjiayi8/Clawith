import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.api import enterprise as enterprise_api


class DummyResult:
    def __init__(self, values=None):
        self._values = list(values or [])

    def scalar_one_or_none(self):
        return self._values[0] if self._values else None


class RecordingDB:
    def __init__(self, responses=None):
        self.responses = list(responses or [])
        self.committed = False

    async def execute(self, _statement):
        return self.responses.pop(0) if self.responses else DummyResult()

    async def commit(self):
        self.committed = True


def _tenant(tenant_id: uuid.UUID, utility_model_id: uuid.UUID | None = None):
    return SimpleNamespace(
        id=tenant_id,
        default_message_limit=50,
        default_message_period="permanent",
        default_max_agents=2,
        default_agent_ttl_hours=48,
        default_max_llm_calls_per_day=100,
        min_heartbeat_interval_minutes=120,
        default_max_triggers=20,
        min_poll_interval_floor=5,
        max_webhook_rate_ceiling=5,
        utility_model_id=utility_model_id,
    )


@pytest.mark.asyncio
async def test_get_tenant_quotas_platform_admin_can_read_selected_tenant():
    selected_tenant_id = uuid.uuid4()
    tenant = _tenant(selected_tenant_id)
    current_user = SimpleNamespace(role="platform_admin", tenant_id=uuid.uuid4(), identity=None)
    db = RecordingDB([DummyResult([tenant])])

    result = await enterprise_api.get_tenant_quotas(
        tenant_id=str(selected_tenant_id),
        current_user=current_user,
        db=db,
    )

    assert result["default_max_agents"] == 2


@pytest.mark.asyncio
async def test_get_tenant_quotas_org_admin_cannot_read_other_tenant():
    current_user = SimpleNamespace(role="org_admin", tenant_id=uuid.uuid4(), identity=None)
    db = RecordingDB()

    with pytest.raises(HTTPException) as exc:
        await enterprise_api.get_tenant_quotas(
            tenant_id=str(uuid.uuid4()),
            current_user=current_user,
            db=db,
        )

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_update_tenant_quotas_platform_admin_can_set_selected_tenant_utility_model(monkeypatch):
    selected_tenant_id = uuid.uuid4()
    utility_model_id = uuid.uuid4()
    tenant = _tenant(selected_tenant_id)
    current_user = SimpleNamespace(role="platform_admin", tenant_id=uuid.uuid4(), identity=None)
    db = RecordingDB([DummyResult([tenant])])
    monkeypatch.setattr(enterprise_api, "enforce_heartbeat_floor", AsyncMock(return_value=0), raising=False)

    result = await enterprise_api.update_tenant_quotas(
        enterprise_api.TenantQuotaUpdate(utility_model_id=str(utility_model_id)),
        tenant_id=str(selected_tenant_id),
        current_user=current_user,
        db=db,
    )

    assert tenant.utility_model_id == utility_model_id
    assert db.committed is True
    assert result["message"] == "Tenant quotas updated"


@pytest.mark.asyncio
async def test_update_tenant_quotas_org_admin_cannot_write_other_tenant():
    current_user = SimpleNamespace(role="org_admin", tenant_id=uuid.uuid4(), identity=None)
    db = RecordingDB()

    with pytest.raises(HTTPException) as exc:
        await enterprise_api.update_tenant_quotas(
            enterprise_api.TenantQuotaUpdate(default_max_agents=5),
            tenant_id=str(uuid.uuid4()),
            current_user=current_user,
            db=db,
        )

    assert exc.value.status_code == 403
