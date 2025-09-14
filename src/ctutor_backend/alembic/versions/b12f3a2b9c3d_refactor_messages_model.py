from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b12f3a2b9c3d'
down_revision = 'fix_result_constraint_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Rename tables if they exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'codeability_message' in tables and 'message' not in tables:
        op.rename_table('codeability_message', 'message')
    if 'codeability_message_read' in tables and 'message_read' not in tables:
        op.rename_table('codeability_message_read', 'message_read')

    # Refresh inspector
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'message' in tables:
        # Add new columns
        op.add_column('message', sa.Column('author_id', postgresql.UUID(), nullable=True))
        op.add_column('message', sa.Column('user_id', postgresql.UUID(), nullable=True))
        op.add_column('message', sa.Column('course_member_id', postgresql.UUID(), nullable=True))
        op.add_column('message', sa.Column('course_submission_group_id', postgresql.UUID(), nullable=True))
        op.add_column('message', sa.Column('course_group_id', postgresql.UUID(), nullable=True))

        # Fix parent fk to new table name if needed
        # Recreate FK for parent_id referencing message
        fk_names = [fk['name'] for fk in inspector.get_foreign_keys('message') if fk.get('name')]
        if 'codeability_message_parent_id_fkey' in (fk_names or []):
            op.drop_constraint('codeability_message_parent_id_fkey', 'message', type_='foreignkey')
            op.create_foreign_key(None, 'message', 'message', ['parent_id'], ['id'], ondelete='CASCADE', onupdate='RESTRICT')

        # Backfill author_id from old transmitter_course_member_id
        columns = [col['name'] for col in inspector.get_columns('message')]
        if 'transmitter_course_member_id' in columns:
            op.execute(
                """
                UPDATE message m
                SET author_id = u.id
                FROM course_member cm
                JOIN "user" u ON u.id = cm.user_id
                WHERE m.transmitter_course_member_id = cm.id AND m.author_id IS NULL
                """
            )
            # Make author_id not null after backfill
            op.alter_column('message', 'author_id', existing_type=postgresql.UUID(), nullable=False)

            # Drop old column and course_id (no longer needed)
            if 'course_id' in columns:
                # Drop potential index referencing course_id if exists; ignore errors in migration if not found
                try:
                    op.drop_index('msg_course_archived_idx', table_name='message')
                except Exception:
                    pass
                op.drop_column('message', 'course_id')
            op.drop_column('message', 'transmitter_course_member_id')
        else:
            # Ensure author_id is not null for new installs
            op.alter_column('message', 'author_id', existing_type=postgresql.UUID(), nullable=False)

        # Create new foreign keys
        op.create_foreign_key(None, 'message', 'user', ['author_id'], ['id'], ondelete='CASCADE', onupdate='RESTRICT')
        op.create_foreign_key(None, 'message', 'user', ['user_id'], ['id'], ondelete='CASCADE', onupdate='RESTRICT')
        op.create_foreign_key(None, 'message', 'course_member', ['course_member_id'], ['id'], ondelete='CASCADE', onupdate='RESTRICT')
        op.create_foreign_key(None, 'message', 'course_submission_group', ['course_submission_group_id'], ['id'], ondelete='CASCADE', onupdate='RESTRICT')
        op.create_foreign_key(None, 'message', 'course_group', ['course_group_id'], ['id'], ondelete='CASCADE', onupdate='RESTRICT')

        # Indexes
        op.create_index('msg_parent_archived_idx', 'message', ['parent_id', 'archived_at'])
        op.create_index('msg_author_archived_idx', 'message', ['author_id', 'archived_at'])
        op.create_index('msg_user_archived_idx', 'message', ['user_id', 'archived_at'])
        op.create_index('msg_course_member_archived_idx', 'message', ['course_member_id', 'archived_at'])
        op.create_index('msg_submission_group_archived_idx', 'message', ['course_submission_group_id', 'archived_at'])
        op.create_index('msg_course_group_archived_idx', 'message', ['course_group_id', 'archived_at'])

    if 'message_read' in tables:
        # Rename columns if present
        cols = [c['name'] for c in inspector.get_columns('message_read')]
        if 'codeability_message_id' in cols:
            op.alter_column('message_read', 'codeability_message_id', new_column_name='message_id', existing_type=postgresql.UUID())
        if 'course_member_id' in cols:
            # Add new reader_user_id, backfill, set not null, drop old
            op.add_column('message_read', sa.Column('reader_user_id', postgresql.UUID(), nullable=True))
            op.execute(
                """
                UPDATE message_read mr
                SET reader_user_id = u.id
                FROM course_member cm JOIN "user" u ON u.id = cm.user_id
                WHERE mr.course_member_id = cm.id AND mr.reader_user_id IS NULL
                """
            )
            op.alter_column('message_read', 'reader_user_id', existing_type=postgresql.UUID(), nullable=False)
            op.drop_column('message_read', 'course_member_id')

        # Unique index
        try:
            op.drop_index('msg_read_unique_idx', table_name='message_read')
        except Exception:
            pass
        op.create_index('msg_read_unique_idx', 'message_read', ['message_id', 'reader_user_id'], unique=True)


def downgrade() -> None:
    # Best-effort downgrade: keep tables but revert column changes
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'message_read' in tables:
        cols = [c['name'] for c in inspector.get_columns('message_read')]
        if 'reader_user_id' in cols and 'course_member_id' not in cols:
            op.add_column('message_read', sa.Column('course_member_id', postgresql.UUID(), nullable=True))
            try:
                op.drop_index('msg_read_unique_idx', table_name='message_read')
            except Exception:
                pass
            op.create_index('msg_read_unique_idx', 'message_read', ['message_id', 'course_member_id'], unique=True)
            op.drop_column('message_read', 'reader_user_id')

    if 'message' in tables:
        cols = [c['name'] for c in inspector.get_columns('message')]
        if 'author_id' in cols and 'transmitter_course_member_id' not in cols:
            op.add_column('message', sa.Column('transmitter_course_member_id', postgresql.UUID(), nullable=True))
            op.drop_column('message', 'author_id')
        for cname in ['user_id', 'course_member_id', 'course_submission_group_id', 'course_group_id']:
            if cname in cols:
                op.drop_column('message', cname)

    # Table renames back
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    if 'message_read' in tables:
        op.rename_table('message_read', 'codeability_message_read')
    if 'message' in tables:
        op.rename_table('message', 'codeability_message')
