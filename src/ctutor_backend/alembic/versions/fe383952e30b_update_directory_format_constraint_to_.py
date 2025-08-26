"""update_directory_format_constraint_to_allow_dots

Revision ID: fe383952e30b
Revises: 6c2c37382ca7
Create Date: 2025-07-29 13:46:09.633428

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fe383952e30b'
down_revision: Union[str, None] = '6c2c37382ca7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the old constraint
    op.drop_constraint('check_directory_format', 'example', type_='check')
    
    # Add the new constraint that allows dots
    op.create_check_constraint(
        'check_directory_format',
        'example',
        "directory ~ '^[a-zA-Z0-9._-]+$'"
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the new constraint
    op.drop_constraint('check_directory_format', 'example', type_='check')
    
    # Restore the old constraint (without dots)
    op.create_check_constraint(
        'check_directory_format',
        'example',
        "directory ~ '^[a-zA-Z0-9_-]+$'"
    )
