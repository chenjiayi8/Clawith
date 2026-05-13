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
