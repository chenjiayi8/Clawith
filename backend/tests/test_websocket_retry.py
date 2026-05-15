import uuid
from types import SimpleNamespace

import pytest

from app.api.websocket import (
    _find_retry_anchor_message,
    _finalize_onboarding_progress_if_needed,
)


def _msg(role: str, *, hidden: bool = False):
    return SimpleNamespace(
        id=uuid.uuid4(),
        role=role,
        is_hidden=hidden,
        content=f"{role}-content",
    )


def test_retry_anchor_defaults_to_latest_visible_user_message():
    hidden = _msg("user", hidden=True)
    user = _msg("user")
    assistant = _msg("assistant")

    anchor = _find_retry_anchor_message([hidden, user, assistant])

    assert anchor is user


def test_retry_anchor_uses_preceding_user_for_assistant_message_id():
    first_user = _msg("user")
    assistant = _msg("assistant")
    tool = _msg("tool_call")

    anchor = _find_retry_anchor_message(
        [first_user, assistant, tool],
        str(tool.id),
    )

    assert anchor is first_user


def test_retry_anchor_returns_none_for_unknown_message_id():
    user = _msg("user")
    assistant = _msg("assistant")

    anchor = _find_retry_anchor_message(
        [user, assistant],
        str(uuid.uuid4()),
    )

    assert anchor is None


class _DummyAsyncSession:
    def __init__(self):
        self.db = object()

    async def __aenter__(self):
        return self.db

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _DummyWebSocket:
    def __init__(self):
        self.messages = []

    async def send_json(self, payload):
        self.messages.append(payload)


@pytest.mark.asyncio
async def test_finalize_onboarding_progress_marks_completed_when_no_chunk_fired(monkeypatch):
    calls = []
    session = _DummyAsyncSession()

    async def _fake_mark_onboarding_phase(db, agent_id, user_id, phase):
        calls.append((db, agent_id, user_id, phase))

    monkeypatch.setattr("app.api.websocket.async_session", lambda: session)
    monkeypatch.setattr("app.services.onboarding.mark_onboarding_phase", _fake_mark_onboarding_phase)

    websocket = _DummyWebSocket()
    agent_id = uuid.uuid4()
    user_id = uuid.uuid4()

    marked = await _finalize_onboarding_progress_if_needed(
        needs_onboarding_mark=True,
        onboarding_mark_done=False,
        agent_id=agent_id,
        user_id=user_id,
        onboarding_target_phase="greeted",
        websocket=websocket,
    )

    assert marked is True
    assert calls == [(session.db, agent_id, user_id, "greeted")]
    assert websocket.messages == [{"type": "onboarded", "agent_id": str(agent_id)}]
