"""
Replace 'latest' version_tag with concrete latest ExampleVersion.version_tag where possible.

Revision ID: 8e12f3b6c9aa
Revises: 7a4d2c9e81ef
Create Date: 2025-09-15 01:20:00.000000
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '8e12f3b6c9aa'
down_revision = '7a4d2c9e81ef'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update version_tag from 'latest' to actual latest ExampleVersion.version_tag
    # where course_content_deployment.example_identifier matches example.identifier
    op.execute(
        """
        WITH latest AS (
            SELECT ev.example_id, ev.version_tag
            FROM example_version ev
            JOIN (
                SELECT example_id, MAX(version_number) AS max_vn
                FROM example_version
                GROUP BY example_id
            ) mv ON mv.example_id = ev.example_id AND mv.max_vn = ev.version_number
        )
        UPDATE course_content_deployment d
        SET version_tag = l.version_tag
        FROM example e
        JOIN latest l ON l.example_id = e.id
        WHERE d.version_tag = 'latest'
          AND d.example_identifier = e.identifier
        """
    )


def downgrade() -> None:
    # No-op: cannot reliably revert data change
    pass

