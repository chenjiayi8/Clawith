import io
import uuid
import zipfile
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

from app.api import files as files_api
from app.services import skill_map


def _zip_upload(entries: dict[str, bytes], filename: str = "skills.zip") -> UploadFile:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, content in entries.items():
            zf.writestr(path, content)
    buffer.seek(0)
    return UploadFile(filename=filename, file=buffer)


@pytest.mark.asyncio
async def test_preview_zip_reports_root_folder_and_file_count(monkeypatch):
    monkeypatch.setattr(files_api, "check_agent_access", AsyncMock())
    agent_id = uuid.uuid4()
    current_user = SimpleNamespace(id=uuid.uuid4(), role="org_admin", tenant_id=uuid.uuid4(), identity=None)
    upload = _zip_upload({
        "starter-skill/SKILL.md": b"# Starter\n",
        "starter-skill/scripts/run.py": b"print('ok')\n",
    })

    result = await files_api.preview_zip(
        agent_id,
        upload,
        current_user=current_user,
        db=object(),
    )

    assert result["root_folder"] == "starter-skill"
    assert result["total"] == 2
    assert "starter-skill/SKILL.md" in result["files"]


@pytest.mark.asyncio
async def test_extract_zip_strips_archive_root_and_writes_under_skills(monkeypatch, tmp_path):
    monkeypatch.setattr(files_api, "check_agent_access", AsyncMock())
    monkeypatch.setattr(files_api.settings, "AGENT_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(skill_map, "invalidate_cache", lambda _agent_id: None)
    agent_id = uuid.uuid4()
    current_user = SimpleNamespace(id=uuid.uuid4(), role="org_admin", tenant_id=uuid.uuid4(), identity=None)
    upload = _zip_upload({
        "starter-skill/SKILL.md": b"# Starter\n",
        "starter-skill/examples/demo.md": b"demo\n",
    })

    result = await files_api.extract_zip(
        agent_id,
        upload,
        target_path="imports",
        root_name="",
        current_user=current_user,
        db=object(),
    )

    skill_md = tmp_path / str(agent_id) / "skills" / "imports" / "SKILL.md"
    demo_md = tmp_path / str(agent_id) / "skills" / "imports" / "examples" / "demo.md"
    assert result["extracted"] == 2
    assert "imports/SKILL.md" in result["files"]
    assert skill_md.read_text() == "# Starter\n"
    assert demo_md.read_text() == "demo\n"


@pytest.mark.asyncio
async def test_extract_zip_rejects_invalid_root_name(monkeypatch):
    monkeypatch.setattr(files_api, "check_agent_access", AsyncMock())
    agent_id = uuid.uuid4()
    current_user = SimpleNamespace(id=uuid.uuid4(), role="org_admin", tenant_id=uuid.uuid4(), identity=None)
    upload = _zip_upload({"starter-skill/SKILL.md": b"# Starter\n"})

    with pytest.raises(HTTPException) as exc:
        await files_api.extract_zip(
            agent_id,
            upload,
            target_path="",
            root_name="../bad",
            current_user=current_user,
            db=object(),
        )

    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_extract_zip_wraps_flat_archive_under_custom_root_name(monkeypatch, tmp_path):
    monkeypatch.setattr(files_api, "check_agent_access", AsyncMock())
    monkeypatch.setattr(files_api.settings, "AGENT_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(skill_map, "invalidate_cache", lambda _agent_id: None)
    agent_id = uuid.uuid4()
    current_user = SimpleNamespace(id=uuid.uuid4(), role="org_admin", tenant_id=uuid.uuid4(), identity=None)
    upload = _zip_upload({
        "SKILL.md": b"# Flat Skill\n",
        "README.md": b"hello\n",
    })

    result = await files_api.extract_zip(
        agent_id,
        upload,
        target_path="imports",
        root_name="custom-pack",
        current_user=current_user,
        db=object(),
    )

    skill_md = tmp_path / str(agent_id) / "skills" / "imports" / "custom-pack" / "SKILL.md"
    readme_md = tmp_path / str(agent_id) / "skills" / "imports" / "custom-pack" / "README.md"
    assert result["extracted"] == 2
    assert "imports/custom-pack/SKILL.md" in result["files"]
    assert "imports/custom-pack/README.md" in result["files"]
    assert skill_md.read_text() == "# Flat Skill\n"
    assert readme_md.read_text() == "hello\n"


@pytest.mark.asyncio
async def test_extract_zip_wraps_mixed_archive_under_custom_root_name(monkeypatch, tmp_path):
    monkeypatch.setattr(files_api, "check_agent_access", AsyncMock())
    monkeypatch.setattr(files_api.settings, "AGENT_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(skill_map, "invalidate_cache", lambda _agent_id: None)
    agent_id = uuid.uuid4()
    current_user = SimpleNamespace(id=uuid.uuid4(), role="org_admin", tenant_id=uuid.uuid4(), identity=None)
    upload = _zip_upload({
        "root-skill/SKILL.md": b"# Rooted\n",
        "shared/util.py": b"print('util')\n",
        "notes.md": b"mixed\n",
    })

    result = await files_api.extract_zip(
        agent_id,
        upload,
        target_path="imports",
        root_name="bundle",
        current_user=current_user,
        db=object(),
    )

    rooted = tmp_path / str(agent_id) / "skills" / "imports" / "bundle" / "root-skill" / "SKILL.md"
    shared = tmp_path / str(agent_id) / "skills" / "imports" / "bundle" / "shared" / "util.py"
    notes = tmp_path / str(agent_id) / "skills" / "imports" / "bundle" / "notes.md"
    assert result["extracted"] == 3
    assert "imports/bundle/root-skill/SKILL.md" in result["files"]
    assert "imports/bundle/shared/util.py" in result["files"]
    assert "imports/bundle/notes.md" in result["files"]
    assert rooted.read_text() == "# Rooted\n"
    assert shared.read_text() == "print('util')\n"
    assert notes.read_text() == "mixed\n"


@pytest.mark.asyncio
async def test_list_files_hides_openclaw_directory(monkeypatch, tmp_path):
    monkeypatch.setattr(files_api, "check_agent_access", AsyncMock())
    monkeypatch.setattr(files_api.settings, "AGENT_DATA_DIR", str(tmp_path))

    agent_id = uuid.uuid4()
    agent_dir = tmp_path / str(agent_id)
    (agent_dir / ".openclaw").mkdir(parents=True)
    (agent_dir / ".openclaw" / "openclaw.json").write_text('{"env":{"OPENAI_API_KEY":"sk-secret"}}', encoding="utf-8")
    (agent_dir / "workspace").mkdir()
    (agent_dir / "workspace" / "notes.md").write_text("hello", encoding="utf-8")

    current_user = SimpleNamespace(id=uuid.uuid4(), role="member", tenant_id=None, identity=None)

    items = await files_api.list_files(
        agent_id,
        path="",
        current_user=current_user,
        db=object(),
    )

    names = {item.name for item in items}
    assert ".openclaw" not in names
    assert "workspace" in names


@pytest.mark.asyncio
async def test_read_file_blocks_openclaw_config(monkeypatch, tmp_path):
    monkeypatch.setattr(files_api, "check_agent_access", AsyncMock())
    monkeypatch.setattr(files_api.settings, "AGENT_DATA_DIR", str(tmp_path))

    agent_id = uuid.uuid4()
    protected = tmp_path / str(agent_id) / ".openclaw"
    protected.mkdir(parents=True)
    (protected / "openclaw.json").write_text("{}", encoding="utf-8")

    current_user = SimpleNamespace(id=uuid.uuid4(), role="member", tenant_id=None, identity=None)

    with pytest.raises(HTTPException) as exc:
        await files_api.read_file(
            agent_id,
            path=".openclaw/openclaw.json",
            current_user=current_user,
            db=object(),
        )

    assert exc.value.status_code == 403
