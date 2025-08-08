"""refactor_submission_groups_add_grading_table

Revision ID: 366a83771631
Revises: add_deployment_fields
Create Date: 2025-08-08 12:59:51.407081

This migration:
1. Creates new CourseSubmissionGroupGrading table
2. Removes deprecated grading/status fields from CourseSubmissionGroup
3. Removes incorrect course_content_id from CourseSubmissionGroupMember
4. Fixes unique constraints
5. Migrates existing grading data to new table
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '366a83771631'
down_revision: Union[str, None] = 'add_deployment_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the new grading table
    op.create_table('course_submission_group_grading',
        sa.Column('id', postgresql.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('version', sa.BigInteger(), server_default=sa.text('0'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('course_submission_group_id', postgresql.UUID(), nullable=False),
        sa.Column('graded_by_course_member_id', postgresql.UUID(), nullable=False),
        sa.Column('grading', sa.Float(precision=53), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['course_submission_group_id'], ['course_submission_group.id'], 
                                ondelete='CASCADE', onupdate='RESTRICT'),
        sa.ForeignKeyConstraint(['graded_by_course_member_id'], ['course_member.id'], 
                                ondelete='RESTRICT', onupdate='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for the new table
    op.create_index('idx_grading_submission_group', 'course_submission_group_grading', 
                    ['course_submission_group_id'], unique=False)
    op.create_index('idx_grading_graded_by', 'course_submission_group_grading', 
                    ['graded_by_course_member_id'], unique=False)
    
    # Migrate existing grading data from CourseSubmissionGroup to new table if any exists
    # Note: We need to determine who did the grading - using created_by as a fallback
    op.execute("""
        INSERT INTO course_submission_group_grading 
            (course_submission_group_id, graded_by_course_member_id, grading, status, created_at, updated_at)
        SELECT 
            csg.id,
            COALESCE(
                (SELECT cm.id FROM course_member cm 
                 WHERE cm.user_id = csg.created_by 
                 AND cm.course_id = csg.course_id 
                 LIMIT 1),
                (SELECT cm.id FROM course_member cm 
                 WHERE cm.course_id = csg.course_id 
                 AND cm.role IN ('lecturer', 'tutor', 'staff')
                 LIMIT 1)
            ),
            csg.grading,
            csg.status,
            csg.updated_at,  -- Use updated_at as the grading time
            csg.updated_at
        FROM course_submission_group csg
        WHERE csg.grading IS NOT NULL
        AND EXISTS (
            SELECT 1 FROM course_member cm 
            WHERE cm.course_id = csg.course_id
            LIMIT 1
        )
    """)
    
    # Drop the old unique constraint that doesn't make sense
    op.drop_index('course_submission_group_course_content_key', table_name='course_submission_group_member')
    
    # Remove deprecated fields from CourseSubmissionGroupMember
    op.drop_column('course_submission_group_member', 'course_content_id')
    op.drop_column('course_submission_group_member', 'grading')
    
    # Remove deprecated fields from CourseSubmissionGroup
    op.drop_column('course_submission_group', 'grading')
    op.drop_column('course_submission_group', 'status')
    
    # Add useful default properties to CourseSubmissionGroup if not exists
    op.execute("""
        UPDATE course_submission_group 
        SET properties = jsonb_build_object('gitlab', jsonb_build_object())
        WHERE properties IS NULL OR properties = '{}'::jsonb
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Re-add the removed columns
    op.add_column('course_submission_group', 
                  sa.Column('status', sa.String(length=2048), nullable=True))
    op.add_column('course_submission_group', 
                  sa.Column('grading', sa.Float(precision=53), nullable=True))
    
    op.add_column('course_submission_group_member', 
                  sa.Column('grading', sa.Float(precision=53), nullable=True))
    op.add_column('course_submission_group_member', 
                  sa.Column('course_content_id', postgresql.UUID(), nullable=True))
    
    # Restore grading data from the new table back to the old structure
    op.execute("""
        UPDATE course_submission_group csg
        SET grading = subq.grading,
            status = subq.status
        FROM (
            SELECT course_submission_group_id, grading, status,
                   ROW_NUMBER() OVER (PARTITION BY course_submission_group_id ORDER BY created_at DESC) as rn
            FROM course_submission_group_grading
        ) subq
        WHERE csg.id = subq.course_submission_group_id
        AND subq.rn = 1
    """)
    
    # Update course_content_id in member table from submission group
    op.execute("""
        UPDATE course_submission_group_member csgm
        SET course_content_id = csg.course_content_id
        FROM course_submission_group csg
        WHERE csgm.course_submission_group_id = csg.id
    """)
    
    # Make course_content_id not nullable after populating
    op.alter_column('course_submission_group_member', 'course_content_id', nullable=False)
    
    # Add foreign key constraint
    op.create_foreign_key(None, 'course_submission_group_member', 'course_content', 
                          ['course_content_id'], ['id'], ondelete='RESTRICT', onupdate='RESTRICT')
    
    # Recreate the old unique constraint
    op.create_index('course_submission_group_course_content_key', 'course_submission_group_member', 
                    ['course_member_id', 'course_content_id'], unique=True)
    
    # Drop the new grading table
    op.drop_index('idx_grading_graded_by', table_name='course_submission_group_grading')
    op.drop_index('idx_grading_submission_group', table_name='course_submission_group_grading')
    op.drop_table('course_submission_group_grading')
