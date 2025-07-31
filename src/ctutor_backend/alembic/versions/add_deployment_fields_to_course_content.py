"""Add deployment fields to course_content

Revision ID: add_deployment_fields
Revises: fe383952e30b
Create Date: 2025-07-31 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_deployment_fields'
down_revision = 'fe383952e30b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add deployment tracking columns
    op.add_column('course_content', sa.Column('deployed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('course_content', sa.Column('deployment_status', sa.String(length=32), server_default=sa.text("'pending'"), nullable=True))
    op.add_column('course_content', sa.Column('deployment_task_id', sa.String(length=128), nullable=True))
    
    # Add customization tracking columns
    op.add_column('course_content', sa.Column('is_customized', sa.Boolean(), server_default=sa.text('false'), nullable=True))
    op.add_column('course_content', sa.Column('last_customized_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Drop columns
    op.drop_column('course_content', 'last_customized_at')
    op.drop_column('course_content', 'is_customized')
    op.drop_column('course_content', 'deployment_task_id')
    op.drop_column('course_content', 'deployment_status')
    op.drop_column('course_content', 'deployed_at')