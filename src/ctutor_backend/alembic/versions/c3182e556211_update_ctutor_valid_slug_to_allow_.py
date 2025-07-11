"""update_ctutor_valid_slug_to_allow_underscores

Revision ID: c3182e556211
Revises: 27db3ea1442c
Create Date: 2025-07-11 21:57:22.869699

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3182e556211'
down_revision: Union[str, None] = '27db3ea1442c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update ctutor_valid_slug function to allow underscores."""
    op.execute("""
        CREATE OR REPLACE FUNCTION ctutor_valid_slug(value text) 
        RETURNS boolean 
        LANGUAGE plpgsql 
        AS $function$
        BEGIN
            -- Check if the value matches the slug pattern (allow underscores and hyphens)
            RETURN value ~ '^[a-z0-9]+([_-][a-z0-9]+)*$';
        END;
        $function$;
    """)


def downgrade() -> None:
    """Revert ctutor_valid_slug function to original (hyphens only)."""
    op.execute("""
        CREATE OR REPLACE FUNCTION ctutor_valid_slug(value text) 
        RETURNS boolean 
        LANGUAGE plpgsql 
        AS $function$
        BEGIN
            -- Check if the value matches the slug pattern (hyphens only)
            RETURN value ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$';
        END;
        $function$;
    """)
