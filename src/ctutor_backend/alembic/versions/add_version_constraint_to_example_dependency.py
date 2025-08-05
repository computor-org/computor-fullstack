"""Add version_constraint to example_dependency table

Revision ID: add_version_constraint_example_dependency
Revises: fe383952e30b
Create Date: 2025-08-05 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_version_constraint_example_dependency'
down_revision = 'fe383952e30b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add version_constraint column to example_dependency table."""
    op.add_column('example_dependency', 
                  sa.Column('version_constraint', 
                           sa.String(100), 
                           nullable=True,
                           comment="Version constraint (e.g., '>=1.2.0', '^2.1.0', '~1.3.0'). NULL means latest version."))


def downgrade() -> None:
    """Remove version_constraint column from example_dependency table."""
    op.drop_column('example_dependency', 'version_constraint')