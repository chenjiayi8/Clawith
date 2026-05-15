import asyncio
from pathlib import Path
import shutil

from app import main
import pytest


def test_load_ss_nodes_from_config_skips_directory(tmp_path: Path):
    cfg_dir = tmp_path / "ss-nodes.json"
    cfg_dir.mkdir()

    nodes = main._load_ss_nodes_from_config(str(cfg_dir))

    assert nodes is None


def test_load_ss_nodes_from_config_reads_valid_json(tmp_path: Path):
    cfg_file = tmp_path / "ss-nodes.json"
    cfg_file.write_text(
        '[{"server":"1.2.3.4","port":1080,"password":"secret","method":"chacha20-ietf-poly1305","label":"test"}]'
    )

    nodes = main._load_ss_nodes_from_config(str(cfg_file))

    assert nodes == [
        {
            "server": "1.2.3.4",
            "port": 1080,
            "password": "secret",
            "method": "chacha20-ietf-poly1305",
            "label": "test",
        }
    ]


@pytest.mark.asyncio
async def test_start_ss_local_skips_env_fallback_when_invalid_config_exists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    cfg_dir = tmp_path / "ss-nodes.json"
    cfg_dir.mkdir()

    async def fail_if_called(*args, **kwargs):
        raise AssertionError("ss-local should not start when the config path exists but is invalid")

    monkeypatch.setenv("SS_CONFIG_FILE", str(cfg_dir))
    monkeypatch.setenv("SS_SERVER", "1.2.3.4")
    monkeypatch.setenv("SS_PASSWORD", "secret")
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/ss-local" if name == "ss-local" else None)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", fail_if_called)

    await main._start_ss_local()
