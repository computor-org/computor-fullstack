"""add_partial_unique_indexes_for_failed_results

Revision ID: c887b1c8c80d
Revises: 366a83771631
Create Date: 2025-08-26 14:28:40.462436

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c887b1c8c80d'
down_revision: Union[str, None] = '366a83771631'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Replace unique constraints with partial unique indexes that allow multiple failed results.
    
    This migration:
    1. Drops the existing unique constraints on (course_member_id, version_identifier) 
       and (course_submission_group_id, version_identifier)
    2. Creates new partial unique indexes that only enforce uniqueness for non-failed results
    
    This allows multiple results with the same version_identifier when status is FAILED (1),
    CRASHED (6), or CANCELLED (2), while still preventing duplicate successful or running results.
    """
    # Drop existing unique indexes
    op.drop_index('result_version_identifier_member_key', table_name='result')
    op.drop_index('result_version_identifier_group_key', table_name='result')
    
    # Create partial unique indexes that exclude failed states
    # Status values: COMPLETED=0, FAILED=1, CANCELLED=2, SCHEDULED=3, PENDING=4, 
    #                RUNNING=5, CRASHED=6, PAUSED=7, CANCELLING=8
    # We allow multiple results when status IN (1=FAILED, 2=CANCELLED, 6=CRASHED)
    op.execute("""
        CREATE UNIQUE INDEX result_version_identifier_member_partial_key 
        ON result (course_member_id, version_identifier) 
        WHERE status NOT IN (1, 2, 6)
    """)
    
    op.execute("""
        CREATE UNIQUE INDEX result_version_identifier_group_partial_key 
        ON result (course_submission_group_id, version_identifier) 
        WHERE status NOT IN (1, 2, 6)
    """)


def downgrade() -> None:
    """
    Restore original unique constraints.
    
    Note: This downgrade may fail if there are multiple results with the same 
    version_identifier in the database. You may need to clean up duplicate data first.
    """
    # Drop partial unique indexes
    op.drop_index('result_version_identifier_member_partial_key', table_name='result')
    op.drop_index('result_version_identifier_group_partial_key', table_name='result')
    
    # Recreate original unique indexes
    op.create_index('result_version_identifier_member_key', 'result', 
                    ['course_member_id', 'version_identifier'], unique=True)
    op.create_index('result_version_identifier_group_key', 'result', 
                    ['course_submission_group_id', 'version_identifier'], unique=True)
