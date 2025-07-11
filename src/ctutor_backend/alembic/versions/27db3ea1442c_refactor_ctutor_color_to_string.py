"""refactor_ctutor_color_to_string

Revision ID: 27db3ea1442c
Revises: 6c2c37382ca7
Create Date: 2025-07-11 19:15:35.771162

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '27db3ea1442c'
down_revision: Union[str, None] = '6c2c37382ca7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Convert ctutor_color from ENUM to VARCHAR(255)."""
    
    # Step 1: Add temporary column
    op.add_column('course_content_type', sa.Column('color_temp', sa.String(255), nullable=True))
    
    # Step 2: Copy data from enum to string (preserving existing values)
    op.execute("""
        UPDATE course_content_type 
        SET color_temp = CAST(color AS TEXT)
        WHERE color IS NOT NULL
    """)
    
    # Step 3: Drop the old enum column
    op.drop_column('course_content_type', 'color')
    
    # Step 4: Rename temp column to color
    op.alter_column('course_content_type', 'color_temp', new_column_name='color')
    
    # Step 5: Drop the unused enum type (if no other tables use it)
    op.execute("DROP TYPE IF EXISTS ctutor_color CASCADE")


def downgrade() -> None:
    """Downgrade schema - Convert ctutor_color from VARCHAR(255) back to ENUM."""
    
    # Step 1: Recreate the enum type
    op.execute("""
        CREATE TYPE ctutor_color AS ENUM (
            'red', 'orange', 'amber', 'yellow', 'lime', 'green', 'emerald', 
            'teal', 'cyan', 'sky', 'blue', 'indigo', 'violet', 'purple', 
            'fuchsia', 'pink', 'rose'
        )
    """)
    
    # Step 2: Add temporary enum column
    op.add_column('course_content_type', sa.Column('color_temp', sa.Enum('red', 'orange', 'amber', 'yellow', 'lime', 'green', 'emerald', 'teal', 'cyan', 'sky', 'blue', 'indigo', 'violet', 'purple', 'fuchsia', 'pink', 'rose', name='ctutor_color'), nullable=True))
    
    # Step 3: Copy data back (only valid enum values)
    op.execute("""
        UPDATE course_content_type 
        SET color_temp = CAST(color AS ctutor_color)
        WHERE color IN ('red', 'orange', 'amber', 'yellow', 'lime', 'green', 'emerald', 'teal', 'cyan', 'sky', 'blue', 'indigo', 'violet', 'purple', 'fuchsia', 'pink', 'rose')
    """)
    
    # Step 4: Drop string column
    op.drop_column('course_content_type', 'color')
    
    # Step 5: Rename temp column back to color
    op.alter_column('course_content_type', 'color_temp', new_column_name='color')
