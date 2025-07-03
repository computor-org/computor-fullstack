"""remove trigger

Revision ID: 4fa21cbdd53b
Revises: 389c240e4426
Create Date: 2025-06-15 12:41:36.089449

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4fa21cbdd53b'
down_revision: Union[str, None] = '389c240e4426'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade():
    # 1) Trigger before_insert_or_update entfernen
    op.execute('DROP TRIGGER IF EXISTS before_insert_or_update ON public."user";')
    # 2) Trigger update_timestamps entfernen
    op.execute('DROP TRIGGER IF EXISTS update_timestamps ON public."user";')
    # 3) Funktion user_before_insert_or_update entfernen
    op.execute('DROP FUNCTION IF EXISTS public.user_before_insert_or_update() CASCADE;')


def downgrade():
    # 1) Funktion wieder anlegen
    op.execute("""
    CREATE OR REPLACE FUNCTION public.user_before_insert_or_update()
    RETURNS trigger AS
    $$
    BEGIN
        IF NEW.auth_token IS NOT NULL THEN
            NEW.auth_token := crypt(NEW.auth_token, gen_salt('bf', 12));
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # 2) Trigger update_timestamps wieder anlegen
    op.execute("""
    CREATE TRIGGER update_timestamps
      BEFORE INSERT OR UPDATE
      ON public."user"
      FOR EACH ROW
      EXECUTE FUNCTION public.ctutor_update_timestamps();
    """)

    # 3) Trigger before_insert_or_update wieder anlegen
    op.execute("""
    CREATE TRIGGER before_insert_or_update
      BEFORE INSERT OR UPDATE
      ON public."user"
      FOR EACH ROW
      EXECUTE FUNCTION public.user_before_insert_or_update();
    """)