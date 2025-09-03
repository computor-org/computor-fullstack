"""Add example_version_id and remove example_version from course_content

Revision ID: add_example_version_id
Revises: migrate_to_example_version_id
Create Date: 2024-01-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_example_version_id'
down_revision = 'c887b1c8c80d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the trigger if it exists (it depends on example_id which we're keeping)
    connection = op.get_bind()
    connection.execute(sa.text("DROP TRIGGER IF EXISTS trg_validate_course_content_example ON course_content"))
    
    # Add the new example_version_id column
    op.add_column('course_content', 
        sa.Column('example_version_id', postgresql.UUID, nullable=True))
    
    # Create foreign key constraint for example_version_id
    op.create_foreign_key(
        'fk_course_content_example_version_id', 
        'course_content', 
        'example_version',
        ['example_version_id'], 
        ['id'],
        ondelete='SET NULL'
    )
    
    # Migrate existing data: match example_id + example_version to find the right example_version.id
    connection.execute(sa.text("""
        UPDATE course_content cc
        SET example_version_id = ev.id
        FROM example_version ev
        WHERE cc.example_id = ev.example_id
        AND cc.example_version = ev.version_tag
        AND cc.example_id IS NOT NULL
        AND cc.example_version IS NOT NULL
    """))
    
    # For any records with example_id but no matching version, use the latest version
    connection.execute(sa.text("""
        UPDATE course_content cc
        SET example_version_id = (
            SELECT ev.id
            FROM example_version ev
            WHERE ev.example_id = cc.example_id
            ORDER BY ev.version_number DESC
            LIMIT 1
        )
        WHERE cc.example_id IS NOT NULL
        AND cc.example_version IS NOT NULL
        AND cc.example_version_id IS NULL
    """))
    
    # Drop the old example_version column
    op.drop_column('course_content', 'example_version')
    
    # Create index on the new column for performance
    op.create_index('idx_course_content_example_version_id', 'course_content', ['example_version_id'])
    
    # Note: The trigger trg_validate_course_content_example was dropped.
    # If validation is still needed, create a new trigger that validates both example_id and example_version_id.


def downgrade() -> None:
    # Add back the example_version column
    op.add_column('course_content',
        sa.Column('example_version', sa.String(64), nullable=True))
    
    # Migrate data back
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE course_content cc
        SET example_version = ev.version_tag
        FROM example_version ev
        WHERE cc.example_version_id = ev.id
        AND cc.example_version_id IS NOT NULL
    """))
    
    # Drop the index
    op.drop_index('idx_course_content_example_version_id', 'course_content')
    
    # Drop the foreign key constraint
    op.drop_constraint('fk_course_content_example_version_id', 'course_content', type_='foreignkey')
    
    # Drop the example_version_id column
    op.drop_column('course_content', 'example_version_id')