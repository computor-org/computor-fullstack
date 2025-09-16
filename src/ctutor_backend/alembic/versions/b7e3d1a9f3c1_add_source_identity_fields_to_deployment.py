"""
Add source identity fields (identifier + version_tag) to deployments and history.

Revision ID: b7e3d1a9f3c1
Revises: 6c2c37382ca7
Create Date: 2025-09-15 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy_utils.types.ltree import LtreeType


# revision identifiers, used by Alembic.
revision = 'b7e3d1a9f3c1'
down_revision = '6c2c37382ca7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure ltree extension exists (no-op if already present)
    op.execute("CREATE EXTENSION IF NOT EXISTS ltree;")

    # course_content_deployment: add source_example_identifier + source_version_tag
    op.add_column(
        'course_content_deployment',
        sa.Column('source_example_identifier', LtreeType(), nullable=True, comment='Hierarchical identifier (ltree) of the example source; present even if no DB Example exists')
    )
    op.add_column(
        'course_content_deployment',
        sa.Column('source_version_tag', sa.String(length=64), nullable=True, comment='Version tag of the example source; may be null for custom assignments')
    )
    op.create_index('idx_deployment_source_identifier', 'course_content_deployment', ['source_example_identifier'], unique=False)
    op.create_index('idx_deployment_source_tag', 'course_content_deployment', ['source_version_tag'], unique=False)

    # deployment_history: snapshot fields example_identifier + version_tag
    op.add_column(
        'deployment_history',
        sa.Column('example_identifier', LtreeType(), nullable=True, comment='Hierarchical identifier (ltree) of the example at action time')
    )
    op.add_column(
        'deployment_history',
        sa.Column('version_tag', sa.String(length=64), nullable=True, comment='Version tag of the example at action time')
    )
    op.create_index('idx_history_example_identifier', 'deployment_history', ['example_identifier'], unique=False)
    op.create_index('idx_history_version_tag', 'deployment_history', ['version_tag'], unique=False)


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_history_version_tag', table_name='deployment_history')
    op.drop_index('idx_history_example_identifier', table_name='deployment_history')
    op.drop_index('idx_deployment_source_tag', table_name='course_content_deployment')
    op.drop_index('idx_deployment_source_identifier', table_name='course_content_deployment')

    # Drop columns
    op.drop_column('deployment_history', 'version_tag')
    op.drop_column('deployment_history', 'example_identifier')
    op.drop_column('course_content_deployment', 'source_version_tag')
    op.drop_column('course_content_deployment', 'source_example_identifier')

