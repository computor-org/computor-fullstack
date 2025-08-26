"""Add basic deployment tracking fields to course_content

Revision ID: add_deployment_fields
Revises: fe383952e30b
Create Date: 2025-07-31 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_deployment_fields'
down_revision = 'fe383952e30b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add basic deployment tracking columns
    op.add_column('course_content', sa.Column('deployed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('course_content', sa.Column('deployment_status', sa.String(length=32), server_default=sa.text("'pending'"), nullable=True))


def downgrade() -> None:
    # Drop columns
    op.drop_column('course_content', 'deployment_status')
    op.drop_column('course_content', 'deployed_at')