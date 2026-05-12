"""Create notifications table for legacy installs.

Revision ID: add_notifications_table
Revises: add_workspace_deployment_tables
Create Date: 2026-05-12
"""

from alembic import op


revision = "add_notifications_table"
down_revision = "add_workspace_deployment_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id),
            agent_id UUID REFERENCES agents(id),
            type VARCHAR(50) NOT NULL,
            title VARCHAR(200) NOT NULL,
            body TEXT NOT NULL DEFAULT '',
            link VARCHAR(500),
            ref_id UUID,
            sender_name VARCHAR(100),
            is_read BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )

    for statement in [
        "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id)",
        "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS agent_id UUID REFERENCES agents(id)",
        "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS type VARCHAR(50)",
        "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS title VARCHAR(200)",
        "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS body TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS link VARCHAR(500)",
        "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS ref_id UUID",
        "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS sender_name VARCHAR(100)",
        "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS is_read BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now()",
        "ALTER TABLE notifications ALTER COLUMN user_id DROP NOT NULL",
    ]:
        op.execute(statement)

    op.execute("CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_notifications_agent_id ON notifications(agent_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_notifications_created_at ON notifications(created_at)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS notifications")
