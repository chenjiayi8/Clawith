import sys
import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException


class _NoopLogger:
    def __getattr__(self, _name):
        return lambda *args, **kwargs: None


sys.modules.setdefault("loguru", SimpleNamespace(logger=_NoopLogger()))

from app.api import enterprise as enterprise_api  # noqa: E402


class DummyResult:
    def __init__(self, values=None, scalar_value=None):
        self._values = list(values or [])
        self._scalar_value = scalar_value

    def scalar_one_or_none(self):
        if self._values:
            return self._values[0]
        return self._scalar_value


class RecordingDB:
    def __init__(self, responses=None):
        self.responses = list(responses or [])
        self.committed = False

    async def execute(self, _statement, _params=None):
        if not self.responses:
            raise AssertionError("unexpected execute() call")
        return self.responses.pop(0)

    async def commit(self):
        self.committed = True


@pytest.mark.asyncio
async def test_update_tenant_quotas_rejects_unknown_utility_model():
    tenant_id = uuid.uuid4()
    current_user = SimpleNamespace(tenant_id=tenant_id)
    tenant = SimpleNamespace(id=tenant_id, utility_model_id=None)
    db = RecordingDB(
        responses=[
            DummyResult([tenant]),
            DummyResult([], scalar_value=None),
        ]
    )

    with pytest.raises(HTTPException) as exc:
        await enterprise_api.update_tenant_quotas(
            data=enterprise_api.TenantQuotaUpdate(utility_model_id=str(uuid.uuid4())),
            current_user=current_user,
            db=db,
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "Model not found"
    assert db.committed is False


@pytest.mark.asyncio
async def test_update_tenant_quotas_rejects_disabled_or_wrong_tenant_utility_model():
    tenant_id = uuid.uuid4()
    current_user = SimpleNamespace(tenant_id=tenant_id)

    cases = [
        SimpleNamespace(id=uuid.uuid4(), tenant_id=tenant_id, enabled=False),
        SimpleNamespace(id=uuid.uuid4(), tenant_id=uuid.uuid4(), enabled=True),
        SimpleNamespace(id=uuid.uuid4(), tenant_id=None, enabled=True),
    ]

    for model in cases:
        tenant = SimpleNamespace(id=tenant_id, utility_model_id=None)
        db = RecordingDB(
            responses=[
                DummyResult([tenant]),
                DummyResult([model]),
            ]
        )

        with pytest.raises(HTTPException) as exc:
            await enterprise_api.update_tenant_quotas(
                data=enterprise_api.TenantQuotaUpdate(utility_model_id=str(model.id)),
                current_user=current_user,
                db=db,
            )

        assert exc.value.status_code == 400
        assert db.committed is False


@pytest.mark.asyncio
async def test_platform_admin_can_target_selected_tenant_quotas():
    admin_tenant_id = uuid.uuid4()
    target_tenant_id = uuid.uuid4()
    current_user = SimpleNamespace(role="platform_admin", tenant_id=admin_tenant_id)
    tenant = SimpleNamespace(id=target_tenant_id, utility_model_id=None)
    model = SimpleNamespace(id=uuid.uuid4(), tenant_id=target_tenant_id, enabled=True)
    db = RecordingDB(
        responses=[
            DummyResult([tenant]),
            DummyResult([model]),
        ]
    )

    result = await enterprise_api.update_tenant_quotas(
        data=enterprise_api.TenantQuotaUpdate(utility_model_id=str(model.id)),
        tenant_id=str(target_tenant_id),
        current_user=current_user,
        db=db,
    )

    assert tenant.utility_model_id == model.id
    assert result["message"] == "Tenant quotas updated"
    assert db.committed is True


@pytest.mark.asyncio
async def test_get_tenant_quotas_honors_selected_tenant_for_platform_admin():
    admin_tenant_id = uuid.uuid4()
    target_tenant_id = uuid.uuid4()
    current_user = SimpleNamespace(role="platform_admin", tenant_id=admin_tenant_id)
    tenant = SimpleNamespace(
        id=target_tenant_id,
        default_message_limit=1,
        default_message_period="permanent",
        default_max_agents=2,
        default_agent_ttl_hours=0,
        default_max_llm_calls_per_day=3,
        min_heartbeat_interval_minutes=4,
        default_max_triggers=5,
        min_poll_interval_floor=6,
        max_webhook_rate_ceiling=7,
        utility_model_id=None,
    )
    db = RecordingDB(responses=[DummyResult([tenant])])

    result = await enterprise_api.get_tenant_quotas(
        tenant_id=str(target_tenant_id),
        current_user=current_user,
        db=db,
    )

    assert result["default_message_limit"] == 1
    assert result["utility_model_id"] is None
