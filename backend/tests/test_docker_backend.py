import pytest

from app.services.sandbox.config import SandboxConfig, SandboxType
from app.services.sandbox.local.docker_backend import DockerBackend


class _FakeContainer:
    def __init__(self):
        self.removed = []
        self.killed = False

    def wait(self, timeout):
        assert timeout == 7
        return {"StatusCode": 0}

    def logs(self, stdout, stderr):
        if stdout and not stderr:
            return b"hello from docker backend\n"
        if stderr and not stdout:
            return b""
        raise AssertionError("unexpected logs call")

    def kill(self):
        self.killed = True

    def remove(self, force):
        self.removed.append(force)


class _FakeImages:
    def get(self, image):
        assert image == "python:3.11-slim"

    def pull(self, image):
        raise AssertionError("image pull should not be needed")


class _FakeContainers:
    def __init__(self, container):
        self._container = container
        self.calls = []

    def run(self, image, cmd, **kwargs):
        self.calls.append((image, cmd, kwargs))
        return self._container


class _FakeClient:
    def __init__(self, container):
        self.images = _FakeImages()
        self.containers = _FakeContainers(container)

    def ping(self):
        return True


@pytest.mark.asyncio
async def test_docker_backend_executes_with_detached_container_and_cleans_up():
    container = _FakeContainer()
    backend = DockerBackend(
        SandboxConfig(
            type=SandboxType.DOCKER,
            allow_network=False,
            cpu_limit="0.5",
            memory_limit="256m",
            default_timeout=30,
            max_timeout=60,
        )
    )
    backend._client = _FakeClient(container)

    result = await backend.execute("print('hi')", "python", timeout=7)

    assert result.success is True
    assert result.stdout == "hello from docker backend\n"
    assert result.stderr == ""
    assert result.exit_code == 0

    [(image, cmd, kwargs)] = backend.client.containers.calls
    assert image == "python:3.11-slim"
    assert cmd == ["python3", "-c", "print('hi')"]
    assert kwargs["detach"] is True
    assert kwargs["remove"] is False
    assert kwargs["network_mode"] == "none"
    assert container.removed == [True]


@pytest.mark.asyncio
async def test_docker_backend_treats_read_timed_out_as_timeout_and_kills_container():
    class _TimeoutContainer(_FakeContainer):
        def wait(self, timeout):
            assert timeout == 7
            raise Exception("Read timed out")

    container = _TimeoutContainer()
    backend = DockerBackend(
        SandboxConfig(
            type=SandboxType.DOCKER,
            allow_network=False,
            cpu_limit="0.5",
            memory_limit="256m",
            default_timeout=30,
            max_timeout=60,
        )
    )
    backend._client = _FakeClient(container)

    result = await backend.execute("print('hi')", "python", timeout=7)

    assert result.success is False
    assert result.stdout == ""
    assert result.stderr == ""
    assert result.exit_code == 124
    assert result.error == "Code execution timed out after 7s"
    assert container.killed is True
    assert container.removed == [True]
