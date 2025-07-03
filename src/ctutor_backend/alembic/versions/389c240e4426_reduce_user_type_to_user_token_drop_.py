"""Reduce user_type to user+token, drop auth_token, adjust constraints

Revision ID: 389c240e4426
Revises: 08ac4b0519f8
Create Date: 2025-06-15 12:27:43.147641

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '389c240e4426'
down_revision: Union[str, None] = '08ac4b0519f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

def upgrade():
    # 1) Neuen ENUM-Typ anlegen (mit Schema‑Qualifikation)
    op.execute("CREATE TYPE public.user_type_new AS ENUM ('user', 'token');")

    # 2) Alle alten Abhängigkeiten entfernen:
    #    - Default abwerfen
    op.execute('ALTER TABLE public."user" ALTER COLUMN user_type DROP DEFAULT;')
    #    - CHECK‑Constraints droppen (falls noch nicht geschehen)
    op.drop_constraint('user_token_condition', 'user', type_='check', schema='public')
    op.drop_constraint('user_username_condition', 'user', type_='check', schema='public')

    # 3) Cast der Spalte auf den neuen ENUM (mit USING und Schema‑Qualifikation)
    op.execute("""
        ALTER TABLE public."user"
        ALTER COLUMN user_type
        TYPE public.user_type_new
        USING (user_type::text::public.user_type_new);
    """)

    # 4) Alten ENUM löschen und neuen umbenennen
    op.execute("DROP TYPE public.user_type;")
    op.execute("ALTER TYPE public.user_type_new RENAME TO user_type;")

    # 5) Default neu setzen
    op.execute("""
        ALTER TABLE public."user"
        ALTER COLUMN user_type
        SET DEFAULT 'user'::public.user_type;
    """)

    # 6) Spalte auth_token entfernen
    op.drop_column('user', 'auth_token', schema='public')

    # 7) Neue CHECK‑Constraints anlegen
    op.create_check_constraint(
        'ck_user_token_expiration',
        'user',
        "(user_type <> 'token') OR (token_expiration IS NOT NULL)",
        schema='public'
    )
