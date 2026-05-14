from pathlib import Path

from app import main


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
