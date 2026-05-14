import ast
from pathlib import Path


def _imported_model_modules(source_text: str) -> set[str]:
    tree = ast.parse(source_text)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("app.models."):
            imported.add(node.module.removeprefix("app.models.").split(".", 1)[0])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("app.models."):
                    imported.add(alias.name.removeprefix("app.models.").split(".", 1)[0])
    return imported


def test_alembic_env_imports_all_model_modules_for_initial_schema():
    repo_root = Path(__file__).resolve().parents[1]
    env_text = (repo_root / "alembic" / "env.py").read_text(encoding="utf-8")
    model_modules = {
        path.stem
        for path in (repo_root / "app" / "models").glob("*.py")
        if path.stem != "__init__"
    }

    missing = sorted(model_modules - _imported_model_modules(env_text))
    assert missing == []


def test_bootstrap_db_imports_all_model_modules_before_create_all():
    repo_root = Path(__file__).resolve().parents[1]
    bootstrap_text = (repo_root / "app" / "scripts" / "bootstrap_db.py").read_text(encoding="utf-8")
    model_modules = {
        path.stem
        for path in (repo_root / "app" / "models").glob("*.py")
        if path.stem != "__init__"
    }

    missing = sorted(model_modules - _imported_model_modules(bootstrap_text))
    assert missing == []
