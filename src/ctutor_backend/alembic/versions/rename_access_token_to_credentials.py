"""Rename access_token to access_credentials

Revision ID: rename_access_token_to_credentials
Revises: add_example_repository_source_type
Create Date: 2025-07-29 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'rename_access_token_to_credentials'
down_revision = 'add_example_repository_source_type'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename the column from access_token to access_credentials
    op.alter_column('example_repository', 'access_token',
                    new_column_name='access_credentials',
                    existing_type=sa.Text(),
                    existing_nullable=True,
                    comment='Encrypted access credentials (Git token, MinIO credentials JSON, etc.)')


def downgrade() -> None:
    # Rename back to access_token
    op.alter_column('example_repository', 'access_credentials',
                    new_column_name='access_token',
                    existing_type=sa.Text(),
                    existing_nullable=True,
                    comment='Encrypted token for accessing private repositories')