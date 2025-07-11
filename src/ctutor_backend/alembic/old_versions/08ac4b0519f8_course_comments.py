"""course comments

Revision ID: 08ac4b0519f8
Revises: 98a7ea29348b
Create Date: 2025-03-24 12:50:01.029546

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm

from model.models import CourseMemberComment


# revision identifiers, used by Alembic.
revision: str = '08ac4b0519f8'
down_revision: Union[str, None] = '98a7ea29348b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    #session = orm.Session(bind=bind)

    CourseMemberComment.__table__.create(bind)

    op.execute("""
        CREATE TRIGGER update_timestamps
        BEFORE INSERT OR UPDATE
        ON course_member_comment
        FOR EACH ROW
        EXECUTE FUNCTION public.ctutor_update_timestamps();
    """)


def downgrade() -> None:
    op.drop_table(CourseMemberComment.__table__)
    op.execute("DROP TRIGGER IF EXISTS update_timestamps ON course_member_comment;")
