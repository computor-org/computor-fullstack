"""Remove redundant example_id from course_content

Revision ID: remove_redundant_example_id
Revises: add_course_content_deployment
Create Date: 2024-01-15

This migration removes the redundant example_id column from course_content
since we can get it via example_version_id -> example_version.example_id
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'remove_redundant_example_id'
down_revision = 'add_course_content_deployment'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Remove redundant example_id column from course_content.
    The example_id can be accessed through example_version.example_id
    """
    
    # Drop the foreign key constraint first
    op.drop_constraint('course_content_example_id_fkey', 'course_content', type_='foreignkey')
    
    # Drop the column
    op.drop_column('course_content', 'example_id')
    
    # Also clean up the deprecated deployment columns since we have the new tables
    # These are now handled by course_content_deployment table
    op.drop_column('course_content', 'deployment_status')
    op.drop_column('course_content', 'deployed_at')
    
    # The example_version_id stays but should only be used via deployment table
    # Add comment to indicate this
    op.execute("""
        COMMENT ON COLUMN course_content.example_version_id IS 
        'DEPRECATED: Access via course_content_deployment.example_version_id instead. Will be removed in future migration.';
    """)


def downgrade() -> None:
    """
    Restore example_id, deployment_status, and deployed_at columns.
    """
    
    # Restore example_id column
    op.add_column('course_content',
        sa.Column('example_id', postgresql.UUID, nullable=True)
    )
    
    # Restore foreign key constraint
    op.create_foreign_key(
        'course_content_example_id_fkey',
        'course_content',
        'example',
        ['example_id'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # Restore deployment columns
    op.add_column('course_content',
        sa.Column('deployment_status', sa.String(32), server_default='pending')
    )
    
    op.add_column('course_content',
        sa.Column('deployed_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # Populate example_id from example_version relationship
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE course_content cc
        SET example_id = ev.example_id
        FROM example_version ev
        WHERE cc.example_version_id = ev.id
        AND cc.example_version_id IS NOT NULL
    """))
    
    # Populate deployment fields from deployment table
    connection.execute(sa.text("""
        UPDATE course_content cc
        SET 
            deployment_status = cd.deployment_status,
            deployed_at = cd.deployed_at
        FROM course_content_deployment cd
        WHERE cc.id = cd.course_content_id
    """))
    
    # Remove comment from example_version_id
    op.execute("""
        COMMENT ON COLUMN course_content.example_version_id IS NULL;
    """)