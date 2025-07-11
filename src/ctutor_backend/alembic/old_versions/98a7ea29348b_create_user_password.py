"""create user password

Revision ID: 98a7ea29348b
Revises: 
Create Date: 2025-03-20 14:43:48.449096

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '98a7ea29348b'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user', sa.Column('password', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('user', 'password')
