import sys
import uuid
from types import SimpleNamespace

import pytest


class _NoopLogger:
    def __getattr__(self, _name):
        return lambda *args, **kwargs: None


sys.modules.setdefault("loguru", SimpleNamespace(logger=_NoopLogger()))

from app.api import websocket as websocket_api  # noqa: E402
from app.services import agent_context, skill_map  # noqa: E402


def _write_skill(
    root,
    agent_id: uuid.UUID,
    folder: str = "qa",
    *,
    description: str = "Regression test skill",
) -> str:
    skill_dir = root / str(agent_id) / "skills" / folder
    skill_dir.mkdir(parents=True, exist_ok=True)
    content = f"""---
name: QA
description: {description}
emoji: test
---
# QA

Use this for regression testing.
"""
    (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
    return content


def test_get_skill_map_uses_canonical_agent_workspace(tmp_path, monkeypatch):
    agent_id = uuid.uuid4()
    _write_skill(tmp_path, agent_id)

    monkeypatch.setattr(agent_context, "PERSISTENT_DATA", tmp_path)
    skill_map.invalidate_cache(agent_id)

    result = skill_map.get_skill_map(agent_id)

    assert result == {
        "qa": {
            "name": "QA",
            "description": "Regression test skill",
            "emoji": "test",
            "file": "qa/SKILL.md",
        }
    }


@pytest.mark.asyncio
async def test_websocket_skill_resolution_prefers_canonical_workspace(tmp_path, monkeypatch):
    agent_id = uuid.uuid4()
    canonical_root = tmp_path / "canonical"
    legacy_root = tmp_path / "legacy"

    canonical_content = _write_skill(
        canonical_root,
        agent_id,
        description="Canonical workspace skill",
    )
    _write_skill(
        legacy_root,
        agent_id,
        description="Legacy workspace skill",
    )

    monkeypatch.setattr(agent_context, "PERSISTENT_DATA", canonical_root)
    monkeypatch.setattr(agent_context, "TOOL_WORKSPACE", legacy_root, raising=False)
    skill_map.invalidate_cache(agent_id)

    content, name, emoji = await websocket_api._resolve_skill_content("qa", agent_id)

    assert content == canonical_content
    assert name == "QA"
    assert emoji == "test"


def test_get_skill_map_for_api_strips_file_paths(tmp_path, monkeypatch):
    agent_id = uuid.uuid4()
    _write_skill(tmp_path, agent_id)

    monkeypatch.setattr(agent_context, "PERSISTENT_DATA", tmp_path)
    skill_map.invalidate_cache(agent_id)

    result = skill_map.get_skill_map_for_api(agent_id)

    assert result == {
        "qa": {
            "name": "QA",
            "description": "Regression test skill",
            "emoji": "test",
        }
    }
