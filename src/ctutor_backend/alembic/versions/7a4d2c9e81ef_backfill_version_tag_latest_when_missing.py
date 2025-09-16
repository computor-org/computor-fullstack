"""
Backfill version_tag='latest' where example_identifier is set but version_tag is NULL.

Revision ID: 7a4d2c9e81ef
Revises: 3c5f0a8c7e2d
Create Date: 2025-09-15 00:55:00.000000
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = '7a4d2c9e81ef'
down_revision = '3c5f0a8c7e2d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # If example_identifier is present but version_tag is NULL, set it to 'latest'
    op.execute(
        """
        UPDATE course_content_deployment
        SET version_tag = 'latest'
        WHERE example_identifier IS NOT NULL
          AND version_tag IS NULL
        """
    )


def downgrade() -> None:
    # No-op: keep data
    pass

