from pathlib import Path


def test_workspace_deployment_head_carries_legacy_schema_compatibility_guards():
    repo_root = Path(__file__).resolve().parents[1]
    migration_text = (
        repo_root / "alembic" / "versions" / "add_workspace_deployment_tables.py"
    ).read_text(encoding="utf-8")

    expected_snippets = [
        "ALTER TABLE workspace_projects ADD COLUMN IF NOT EXISTS tenant_id",
        "ALTER TABLE workspace_projects ADD COLUMN IF NOT EXISTS dockerfile_path",
        "ALTER TABLE agent_triggers ADD COLUMN IF NOT EXISTS is_system",
        "ALTER TABLE agents ADD COLUMN IF NOT EXISTS cache_read_tokens_today",
        "ALTER TABLE agents ADD COLUMN IF NOT EXISTS access_mode",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS identity_id",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS registration_source",
        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS country_region",
        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS sso_enabled",
        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS default_model_id",
        "ALTER TABLE tools ADD COLUMN IF NOT EXISTS source",
        "ALTER TABLE agent_templates ADD COLUMN IF NOT EXISTS default_mcp_servers",
        "ALTER TABLE agent_templates ADD COLUMN IF NOT EXISTS capability_bullets",
        "ALTER TABLE org_members ADD COLUMN IF NOT EXISTS open_id",
        "ALTER TABLE org_members ADD COLUMN IF NOT EXISTS external_id",
        "ALTER TABLE agent_agent_relationships ADD COLUMN IF NOT EXISTS updated_at",
        'for value in ("wechat", "whatsapp", "agentbay")',
        "ALTER TYPE channel_type_enum ADD VALUE IF NOT EXISTS",
    ]

    missing = [snippet for snippet in expected_snippets if snippet not in migration_text]
    assert missing == []
