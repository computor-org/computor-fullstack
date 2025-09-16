"""
Backfill source_example_identifier and source_version_tag on existing deployments.

Revision ID: 9fb0b2a1d4ab
Revises: b7e3d1a9f3c1
Create Date: 2025-09-15 00:20:00.000000
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '9fb0b2a1d4ab'
down_revision = 'b7e3d1a9f3c1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Populate missing source_example_identifier and source_version_tag from example_version/example
    op.execute(
        """
        UPDATE course_content_deployment d
        SET
            source_example_identifier = e.identifier,
            source_version_tag = ev.version_tag
        FROM example_version ev
        JOIN example e ON e.id = ev.example_id
        WHERE d.example_version_id = ev.id
          AND (d.source_example_identifier IS NULL OR d.source_version_tag IS NULL)
        """
    )


def downgrade() -> None:
    # No-op: do not erase backfilled data
    pass

