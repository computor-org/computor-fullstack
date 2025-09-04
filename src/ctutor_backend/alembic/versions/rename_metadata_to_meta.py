"""Rename metadata column to meta in deployment_history table

Revision ID: rename_metadata_to_meta
Revises: remove_redundant_example_id
Create Date: 2024-12-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'rename_metadata_to_meta'
down_revision = 'remove_redundant_example_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Rename 'metadata' column to 'meta' in deployment_history table
    to avoid conflict with SQLAlchemy's reserved attribute.
    """
    op.alter_column('deployment_history', 
                    'metadata', 
                    new_column_name='meta',
                    existing_type=postgresql.JSONB,
                    existing_nullable=True,
                    existing_server_default=sa.text("'{}'::jsonb"),
                    existing_comment='Additional metadata about the action')


def downgrade() -> None:
    """
    Revert column name from 'meta' back to 'metadata'.
    """
    op.alter_column('deployment_history',
                    'meta',
                    new_column_name='metadata',
                    existing_type=postgresql.JSONB,
                    existing_nullable=True,
                    existing_server_default=sa.text("'{}'::jsonb"),
                    existing_comment='Additional metadata about the action')