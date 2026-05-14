import uuid
from types import SimpleNamespace

from app.api.websocket import _find_retry_anchor_message


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
