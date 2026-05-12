"""Add workspace deployment tables and dockerfile path.

Revision ID: add_workspace_deployment_tables
Revises: add_title_edit_util_model
Create Date: 2026-05-11
"""

from alembic import op


revision = "add_workspace_deployment_tables"
down_revision = "add_title_edit_util_model"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE deploy_type_enum AS ENUM ('static', 'container');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE workspace_status_enum AS ENUM (
                'requested', 'building', 'awaiting_approval', 'deployed',
                'failed', 'rejected', 'stopped', 'undeployed'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE bug_source_enum AS ENUM ('health_check', 'user_report');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE bug_status_enum AS ENUM ('open', 'investigating', 'fixed', 'escalated');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    # Legacy-schema compatibility: some long-lived installations still have the
    # pre-refactor shape for users, tenants, tools, triggers, org tables, and
    # agent templates. This migration is the current Alembic head in this
    # branch, so it also normalizes those older schemas before the app boots.
    for value in ("wechat", "whatsapp", "agentbay"):
        op.execute(f"ALTER TYPE channel_type_enum ADD VALUE IF NOT EXISTS '{value}'")

    for statement in [
        "ALTER TABLE agent_triggers ADD COLUMN IF NOT EXISTS is_system BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE agents ADD COLUMN IF NOT EXISTS cache_read_tokens_today INTEGER DEFAULT 0",
        "ALTER TABLE agents ADD COLUMN IF NOT EXISTS cache_read_tokens_month INTEGER DEFAULT 0",
        "ALTER TABLE agents ADD COLUMN IF NOT EXISTS cache_read_tokens_total INTEGER DEFAULT 0",
        "ALTER TABLE agents ADD COLUMN IF NOT EXISTS cache_creation_tokens_today INTEGER DEFAULT 0",
        "ALTER TABLE agents ADD COLUMN IF NOT EXISTS cache_creation_tokens_month INTEGER DEFAULT 0",
        "ALTER TABLE agents ADD COLUMN IF NOT EXISTS cache_creation_tokens_total INTEGER DEFAULT 0",
        "ALTER TABLE agents ADD COLUMN IF NOT EXISTS is_system BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE agents ADD COLUMN IF NOT EXISTS access_mode VARCHAR(20) NOT NULL DEFAULT 'company'",
        "ALTER TABLE agents ADD COLUMN IF NOT EXISTS company_access_level VARCHAR(20) NOT NULL DEFAULT 'use'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS identity_id UUID",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS registration_source VARCHAR(50) DEFAULT 'web'",
        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS country_region VARCHAR(10) NOT NULL DEFAULT '001'",
        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS sso_enabled BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS sso_domain VARCHAR(255)",
        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS a2a_async_enabled BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS default_model_id UUID",
        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS utility_model_id UUID",
        "ALTER TABLE tools ADD COLUMN IF NOT EXISTS source VARCHAR(20) NOT NULL DEFAULT 'builtin'",
        "ALTER TABLE agent_templates ADD COLUMN IF NOT EXISTS default_mcp_servers JSON NOT NULL DEFAULT '[]'::json",
        "ALTER TABLE agent_templates ADD COLUMN IF NOT EXISTS capability_bullets JSON NOT NULL DEFAULT '[]'::json",
        "ALTER TABLE agent_templates ADD COLUMN IF NOT EXISTS bootstrap_content TEXT",
        "ALTER TABLE org_members ADD COLUMN IF NOT EXISTS open_id VARCHAR(100)",
        "ALTER TABLE org_members ADD COLUMN IF NOT EXISTS unionid VARCHAR(100)",
        "ALTER TABLE org_members ADD COLUMN IF NOT EXISTS external_id VARCHAR(100)",
        "ALTER TABLE org_members ADD COLUMN IF NOT EXISTS provider_id UUID",
        "ALTER TABLE org_members ADD COLUMN IF NOT EXISTS user_id UUID",
        "ALTER TABLE org_members ADD COLUMN IF NOT EXISTS name_translit_full VARCHAR(255)",
        "ALTER TABLE org_members ADD COLUMN IF NOT EXISTS name_translit_initial VARCHAR(50)",
        "ALTER TABLE agent_agent_relationships ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ",
        "ALTER TABLE agent_agent_relationships ADD COLUMN IF NOT EXISTS created_by_user_id UUID",
        "ALTER TABLE agent_agent_relationships ADD COLUMN IF NOT EXISTS updated_by_user_id UUID",
    ]:
        op.execute(statement)

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS workspace_projects (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            slug VARCHAR(50) NOT NULL UNIQUE,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL,
            requested_by UUID REFERENCES agents(id) ON DELETE SET NULL,
            requested_by_human VARCHAR(200),
            built_by UUID REFERENCES agents(id) ON DELETE SET NULL,
            deploy_type deploy_type_enum,
            status workspace_status_enum NOT NULL DEFAULT 'requested',
            container_id VARCHAR(100),
            container_image VARCHAR(300),
            container_port INTEGER,
            health_endpoint VARCHAR(200),
            resource_limits JSON,
            dockerfile_path VARCHAR(500),
            auto_fix_attempts INTEGER NOT NULL DEFAULT 0,
            auto_fix_window_start TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute("ALTER TABLE workspace_projects ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL")
    op.execute("ALTER TABLE workspace_projects ADD COLUMN IF NOT EXISTS dockerfile_path VARCHAR(500)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_workspace_projects_slug ON workspace_projects(slug)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_workspace_projects_created_at ON workspace_projects(created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_workspace_projects_tenant_id ON workspace_projects(tenant_id)")
    op.execute(
        """
        UPDATE workspace_projects wp
        SET tenant_id = COALESCE(
            (SELECT a.tenant_id FROM agents a WHERE a.id = wp.built_by),
            (SELECT a.tenant_id FROM agents a WHERE a.id = wp.requested_by)
        )
        WHERE wp.tenant_id IS NULL
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS workspace_bug_reports (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id UUID NOT NULL REFERENCES workspace_projects(id) ON DELETE CASCADE,
            source bug_source_enum NOT NULL,
            description TEXT NOT NULL,
            status bug_status_enum NOT NULL DEFAULT 'open',
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_workspace_bug_reports_project_id ON workspace_bug_reports(project_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_workspace_bug_reports_created_at ON workspace_bug_reports(created_at)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS workspace_bug_reports")
    op.execute("DROP TABLE IF EXISTS workspace_projects")
