"""add workflow_id to deployment

Revision ID: add_workflow_id_col
Revises: rename_metadata_to_meta
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_workflow_id_col'
down_revision = 'rename_metadata_to_meta'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add workflow_id column to course_content_deployment
    op.add_column('course_content_deployment', sa.Column(
        'workflow_id',
        sa.String(length=255),
        nullable=True,
        comment='Current/last Temporal workflow ID for deployment'
    ))


def downgrade() -> None:
    # Remove workflow_id column from course_content_deployment
    op.drop_column('course_content_deployment', 'workflow_id')