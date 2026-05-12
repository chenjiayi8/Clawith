import uuid
from types import SimpleNamespace

import pytest

from app.services import chat_session_service


class DummyResult:
    def __init__(self, value=None):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class RecordingDB:
    def __init__(self, responses=None):
        self.responses = list(responses or [])
        self.statements = []
        self.flushed = False

    async def execute(self, statement):
        self.statements.append(str(statement))
        return self.responses.pop(0) if self.responses else DummyResult()

    async def flush(self):
        self.flushed = True

    def add(self, _value):
        pass


@pytest.mark.asyncio
async def test_get_primary_platform_session_uses_sqlalchemy_boolean_predicates():
    db = RecordingDB([DummyResult(None)])

    await chat_session_service.get_primary_platform_session(db, uuid.uuid4(), uuid.uuid4())

    sql = db.statements[0]
    assert "chat_sessions.is_group IS false" in sql
    assert "chat_sessions.is_primary IS true" in sql


@pytest.mark.asyncio
async def test_ensure_primary_platform_session_promotes_existing_session():
    session = SimpleNamespace(is_primary=False)
    db = RecordingDB([DummyResult(None), DummyResult(session)])

    result = await chat_session_service.ensure_primary_platform_session(db, uuid.uuid4(), uuid.uuid4())

    assert result is session
    assert session.is_primary is True
    assert db.flushed is True
