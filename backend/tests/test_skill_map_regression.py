import sys
import uuid
from types import SimpleNamespace


class _NoopLogger:
    def __getattr__(self, _name):
        return lambda *args, **kwargs: None


sys.modules.setdefault("loguru", SimpleNamespace(logger=_NoopLogger()))

from app.services import agent_context, skill_map  # noqa: E402


def _write_skill(root, agent_id: uuid.UUID, folder: str = "qa") -> str:
    skill_dir = root / str(agent_id) / "skills" / folder
    skill_dir.mkdir(parents=True, exist_ok=True)
    content = """---
name: QA
description: Regression test skill
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
