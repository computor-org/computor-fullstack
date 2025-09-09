"""fix_result_unique_constraint_add_course_content

Revision ID: fix_result_constraint_001
Revises: c887b1c8c80d
Create Date: 2025-01-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fix_result_constraint_001'
down_revision: Union[str, None] = 'add_workflow_id_col'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Fix the unique constraint on result table to include course_content_id.
    
    The current constraint (course_member_id, version_identifier) is too restrictive.
    A student should be able to have multiple results for the same git version 
    but for different course contents (assignments).
    
    This migration:
    1. Drops the existing partial unique indexes
    2. Creates new partial unique indexes that include course_content_id
    """
    
    # Drop the existing partial unique indexes
    op.drop_index('result_version_identifier_member_partial_key', table_name='result')
    op.drop_index('result_version_identifier_group_partial_key', table_name='result')
    
    # Create new partial unique indexes that include course_content_id
    # This allows multiple results for same version but different assignments
    op.create_index(
        'result_version_identifier_member_content_partial_key',
        'result',
        ['course_member_id', 'version_identifier', 'course_content_id'],
        unique=True,
        postgresql_where=sa.text('status NOT IN (1, 2, 6)')  # Exclude FAILED(1), CANCELLED(2), CRASHED(6)
    )
    
    op.create_index(
        'result_version_identifier_group_content_partial_key',
        'result',
        ['course_submission_group_id', 'version_identifier', 'course_content_id'],
        unique=True,
        postgresql_where=sa.text('status NOT IN (1, 2, 6)')  # Exclude FAILED(1), CANCELLED(2), CRASHED(6)
    )


def downgrade() -> None:
    """
    Revert to the original constraints without course_content_id.
    
    WARNING: This downgrade may fail if there are existing results that would
    violate the more restrictive constraint.
    """
    
    # Drop the new indexes
    op.drop_index('result_version_identifier_member_content_partial_key', table_name='result')
    op.drop_index('result_version_identifier_group_content_partial_key', table_name='result')
    
    # Recreate the original indexes
    op.create_index(
        'result_version_identifier_member_partial_key',
        'result',
        ['course_member_id', 'version_identifier'],
        unique=True,
        postgresql_where=sa.text('status NOT IN (1, 2, 6)')
    )
    
    op.create_index(
        'result_version_identifier_group_partial_key',
        'result',
        ['course_submission_group_id', 'version_identifier'],
        unique=True,
        postgresql_where=sa.text('status NOT IN (1, 2, 6)')
    )