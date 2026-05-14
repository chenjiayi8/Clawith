import uuid
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from app.api import websocket as websocket_api
from app.services.agent_manager import AgentManager


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

    async def execute(self, _statement, _params=None):
        if not self.responses:
            raise AssertionError("unexpected execute() call")
        return self.responses.pop(0)


class DummyContainer:
    id = "container-123"


class DummyContainers:
    def __init__(self):
        self.calls = []

    def run(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return DummyContainer()


class DummyDockerClient:
    def __init__(self):
        self.containers = DummyContainers()


@pytest.mark.asyncio
async def test_openclaw_config_does_not_persist_model_api_key(monkeypatch, tmp_path):
    monkeypatch.setattr("app.services.agent_manager.settings.AGENT_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("app.services.agent_manager.get_model_api_key", lambda _model: "sk-secret")

    manager = AgentManager()
    manager.docker_client = DummyDockerClient()

    agent = SimpleNamespace(
        id=uuid.uuid4(),
        name="Review Bot",
        primary_model_id=uuid.uuid4(),
        container_id=None,
        container_port=None,
        status="idle",
        last_active_at=None,
    )
    model = SimpleNamespace(provider="openai", model="gpt-4.1")
    db = RecordingDB([DummyResult([model])])

    await manager.start_container(db, agent)

    config_path = tmp_path / str(agent.id) / ".openclaw" / "openclaw.json"
    config_text = config_path.read_text(encoding="utf-8")
    assert "sk-secret" not in config_text

    _, kwargs = manager.docker_client.containers.calls[0]
    assert kwargs["environment"]["OPENAI_API_KEY"] == "sk-secret"
    assert kwargs["environment"]["OPENCLAW_GATEWAY_TOKEN"]


@pytest.mark.asyncio
async def test_get_chat_history_preserves_hidden_messages(monkeypatch):
    now = datetime.now(UTC)
    hidden = SimpleNamespace(
        id=uuid.uuid4(),
        role="user",
        content="# Loaded skill\nbody",
        created_at=now,
        thinking=None,
        is_hidden=True,
    )
    visible = SimpleNamespace(
        id=uuid.uuid4(),
        role="assistant",
        content="Visible reply",
        created_at=now,
        thinking=None,
        is_hidden=False,
    )
    db = RecordingDB([DummyResult([hidden, visible])])
    current_user = SimpleNamespace(id=uuid.uuid4())

    history = await websocket_api.get_chat_history(
        agent_id=uuid.uuid4(),
        current_user=current_user,
        db=db,
    )

    assert [entry["id"] for entry in history] == [str(hidden.id), str(visible.id)]
    assert history[0]["is_hidden"] is True
    assert history[0]["content"] == hidden.content


def test_docker_compose_agent_network_matches_defined_network():
    repo_root = Path(__file__).resolve().parents[2]
    compose = yaml.safe_load((repo_root / "docker-compose.yml").read_text(encoding="utf-8"))

    backend_network = compose["services"]["backend"]["environment"]["DOCKER_NETWORK"]
    defined_network = compose["networks"]["default"]["name"]

    assert backend_network == defined_network


def test_helm_secrets_template_renders_required_keys():
    repo_root = Path(__file__).resolve().parents[2]
    template = (repo_root / "helm" / "clawith" / "templates" / "secrets.yaml").read_text(encoding="utf-8")

    assert "kind: Secret" in template
    assert "secret-key" in template
    assert "jwt-secret-key" in template


def test_restart_script_keeps_default_postgres_port_and_fails_migrations():
    repo_root = Path(__file__).resolve().parents[2]
    script = (repo_root / "restart.sh").read_text(encoding="utf-8")

    assert 'PG_PORT="$PG_HOST"' not in script
    assert 'if [ "$PG_PORT" = "$PG_HOST" ]; then' in script
    assert ".venv/bin/alembic upgrade head 2>/dev/null || true" not in script


def test_entrypoint_fails_fast_on_migration_error():
    repo_root = Path(__file__).resolve().parents[2]
    script = (repo_root / "backend" / "entrypoint.sh").read_text(encoding="utf-8")

    assert "Continuing startup despite migration failure" not in script
    assert "exit $ALEMBIC_EXIT" in script


def test_backend_startup_does_not_run_metadata_create_all():
    repo_root = Path(__file__).resolve().parents[2]
    main_text = (repo_root / "backend" / "app" / "main.py").read_text(encoding="utf-8")

    assert "run_sync(Base.metadata.create_all)" not in main_text


def test_onboarding_migration_skips_existing_table_creation():
    repo_root = Path(__file__).resolve().parents[2]
    migration_text = (
        repo_root / "backend" / "alembic" / "versions" / "add_user_tenant_onboarding.py"
    ).read_text(encoding="utf-8")

    assert "has_table" in migration_text

