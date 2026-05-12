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
    op.execute("CREATE INDEX IF NOT EXISTS ix_workspace_projects_slug ON workspace_projects(slug)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_workspace_projects_created_at ON workspace_projects(created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_workspace_projects_tenant_id ON workspace_projects(tenant_id)")
    op.execute("ALTER TABLE workspace_projects ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL")
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
