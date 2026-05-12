from pathlib import Path


def test_notifications_table_has_forward_migration():
    repo_root = Path(__file__).resolve().parents[2]
    versions_dir = repo_root / "backend" / "alembic" / "versions"
    create_markers = (
        'create_table("notifications"',
        "create_table('notifications'",
        "CREATE TABLE notifications",
        "CREATE TABLE IF NOT EXISTS notifications",
    )

    has_creator = any(
        any(marker in path.read_text(encoding="utf-8") for marker in create_markers)
        for path in versions_dir.glob("*.py")
    )

    assert has_creator, "Expected an Alembic migration to create notifications for legacy installs"
