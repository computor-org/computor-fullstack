"""
Rename source_* fields on course_content_deployment to example_identifier/version_tag.

Revision ID: 3c5f0a8c7e2d
Revises: 9fb0b2a1d4ab
Create Date: 2025-09-15 00:35:00.000000
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '3c5f0a8c7e2d'
down_revision = '9fb0b2a1d4ab'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old indexes
    op.drop_index('idx_deployment_source_tag', table_name='course_content_deployment')
    op.drop_index('idx_deployment_source_identifier', table_name='course_content_deployment')

    # Rename columns
    op.execute(
        'ALTER TABLE course_content_deployment RENAME COLUMN source_example_identifier TO example_identifier'
    )
    op.execute(
        'ALTER TABLE course_content_deployment RENAME COLUMN source_version_tag TO version_tag'
    )

    # Create new indexes
    op.create_index('idx_deployment_example_identifier', 'course_content_deployment', ['example_identifier'], unique=False)
    op.create_index('idx_deployment_version_tag', 'course_content_deployment', ['version_tag'], unique=False)


def downgrade() -> None:
    # Drop new indexes
    op.drop_index('idx_deployment_version_tag', table_name='course_content_deployment')
    op.drop_index('idx_deployment_example_identifier', table_name='course_content_deployment')

    # Rename columns back
    op.execute(
        'ALTER TABLE course_content_deployment RENAME COLUMN example_identifier TO source_example_identifier'
    )
    op.execute(
        'ALTER TABLE course_content_deployment RENAME COLUMN version_tag TO source_version_tag'
    )

    # Restore old indexes
    op.create_index('idx_deployment_source_identifier', 'course_content_deployment', ['source_example_identifier'], unique=False)
    op.create_index('idx_deployment_source_tag', 'course_content_deployment', ['source_version_tag'], unique=False)

