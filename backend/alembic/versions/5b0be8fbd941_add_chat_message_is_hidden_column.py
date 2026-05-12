"""add chat_message is_hidden column

Revision ID: 5b0be8fbd941
Revises: add_user_tenant_onboarding
Create Date: 2026-03-25 21:47:36.761546
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '5b0be8fbd941'
down_revision: Union[str, None] = 'add_user_tenant_onboarding'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE chat_messages "
        "ADD COLUMN IF NOT EXISTS is_hidden BOOLEAN NOT NULL DEFAULT FALSE"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE chat_messages DROP COLUMN IF EXISTS is_hidden")
