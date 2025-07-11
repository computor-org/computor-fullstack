"""Initial SQLAlchemy schema with PostgreSQL extensions

Revision ID: 001_initial
Revises: 
Create Date: 2025-07-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy_utils import LtreeType


# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
    op.execute("CREATE EXTENSION IF NOT EXISTS ltree;")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    
    # Create enums
    op.execute("""
        CREATE TYPE organization_type AS ENUM ('user', 'community', 'organization');
        CREATE TYPE user_type AS ENUM ('user', 'token');
        CREATE TYPE ctutor_group_type AS ENUM ('fixed', 'dynamic');
        CREATE TYPE ctutor_color AS ENUM (
            'red', 'orange', 'amber', 'yellow', 'lime', 'green', 'emerald', 
            'teal', 'cyan', 'sky', 'blue', 'indigo', 'violet', 'purple', 
            'fuchsia', 'pink', 'rose'
        );
    """)
    
    # Create utility functions
    op.execute("""
        CREATE OR REPLACE FUNCTION ctutor_valid_slug(value text) 
        RETURNS boolean 
        LANGUAGE plpgsql 
        AS $function$
        BEGIN
            RETURN value ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$';
        END;
        $function$;
    """)
    
    op.execute("""
        CREATE OR REPLACE FUNCTION ctutor_on_user_update() 
        RETURNS trigger 
        LANGUAGE plpgsql
        AS $function$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $function$;
    """)
    
    # Create sequences
    op.execute("CREATE SEQUENCE IF NOT EXISTS user_unique_fs_number_seq;")
    
    # Create all tables using the new model structure
    
    # Course content kind
    op.create_table('course_content_kind',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('title', sa.String(255)),
        sa.Column('description', sa.String(4096)),
        sa.Column('has_ascendants', sa.Boolean(), nullable=False),
        sa.Column('has_descendants', sa.Boolean(), nullable=False),
        sa.Column('submittable', sa.Boolean(), nullable=False)
    )
    
    # Course role
    op.create_table('course_role',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('title', sa.String(255)),
        sa.Column('description', sa.String(4096))
    )
    
    # Group
    op.create_table('group',
        sa.Column('id', postgresql.UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column('version', sa.BigInteger, server_default=sa.text("0")),
        sa.Column('created_at', sa.DateTime(True), nullable=False, server_default=sa.text("now()")),
        sa.Column('updated_at', sa.DateTime(True), nullable=False, server_default=sa.text("now()")),
        sa.Column('created_by', postgresql.UUID),
        sa.Column('updated_by', postgresql.UUID),
        sa.Column('properties', postgresql.JSONB),
        sa.Column('title', sa.String(255)),
        sa.Column('description', sa.String(4096)),
        sa.Column('slug', sa.String(255), nullable=False),
        sa.Column('type', postgresql.ENUM('fixed', 'dynamic', name='ctutor_group_type'), server_default=sa.text("'fixed'::ctutor_group_type")),
        sa.CheckConstraint('ctutor_valid_slug((slug)::text)')
    )
    
    # Role
    op.create_table('role',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('title', sa.String(255)),
        sa.Column('description', sa.String(4096)),
        sa.Column('builtin', sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.CheckConstraint("(NOT builtin) OR ((id)::text ~ '^_'::text)"),
        sa.CheckConstraint('(builtin AND ctutor_valid_slug(SUBSTRING(id FROM 2))) OR ((NOT builtin) AND ctutor_valid_slug((id)::text))')
    )
    
    # User
    op.create_table('user',
        sa.Column('id', postgresql.UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column('version', sa.BigInteger, server_default=sa.text("0")),
        sa.Column('created_at', sa.DateTime(True), nullable=False, server_default=sa.text("now()")),
        sa.Column('updated_at', sa.DateTime(True), nullable=False, server_default=sa.text("now()")),
        sa.Column('created_by', postgresql.UUID),
        sa.Column('updated_by', postgresql.UUID),
        sa.Column('properties', postgresql.JSONB),
        sa.Column('number', sa.String(255), unique=True),
        sa.Column('archived_at', sa.DateTime(True)),
        sa.Column('given_name', sa.String(255)),
        sa.Column('family_name', sa.String(255)),
        sa.Column('email', sa.String(320), unique=True),
        sa.Column('user_type', postgresql.ENUM('user', 'token', name='user_type'), nullable=False, server_default=sa.text("'user'::user_type")),
        sa.Column('fs_number', sa.BigInteger, nullable=False, server_default=sa.text("nextval('user_unique_fs_number_seq'::regclass)")),
        sa.Column('token_expiration', sa.DateTime(True)),
        sa.Column('username', sa.String(255), unique=True),
        sa.Column('password', sa.String(255)),
        sa.Column('auth_token', sa.String(4096)),
        sa.CheckConstraint("(user_type <> 'token') OR (token_expiration IS NOT NULL)", name='ck_user_token_expiration'),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['user.id'], ondelete='SET NULL')
    )
    
    # Organization
    op.create_table('organization',
        sa.Column('id', postgresql.UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column('version', sa.BigInteger, server_default=sa.text("0")),
        sa.Column('created_at', sa.DateTime(True), nullable=False, server_default=sa.text("now()")),
        sa.Column('updated_at', sa.DateTime(True), nullable=False, server_default=sa.text("now()")),
        sa.Column('created_by', postgresql.UUID),
        sa.Column('updated_by', postgresql.UUID),
        sa.Column('properties', postgresql.JSONB),
        sa.Column('number', sa.String(255)),
        sa.Column('title', sa.String(255)),
        sa.Column('description', sa.String(4096)),
        sa.Column('archived_at', sa.DateTime(True)),
        sa.Column('email', sa.String(320)),
        sa.Column('telephone', sa.String(255)),
        sa.Column('fax_number', sa.String(255)),
        sa.Column('url', sa.String(2048)),
        sa.Column('postal_code', sa.String(255)),
        sa.Column('street_address', sa.String(1024)),
        sa.Column('locality', sa.String(255)),
        sa.Column('region', sa.String(255)),
        sa.Column('country', sa.String(255)),
        sa.Column('organization_type', postgresql.ENUM('user', 'community', 'organization', name='organization_type'), nullable=False),
        sa.Column('user_id', postgresql.UUID, unique=True),
        sa.Column('path', LtreeType, nullable=False),
        sa.Column('parent_path', LtreeType, sa.Computed("""
            CASE
                WHEN (nlevel(path) > 1) THEN subpath(path, 0, (nlevel(path) - 1))
                ELSE NULL::ltree
            END
        """, persisted=True)),
        sa.CheckConstraint("((organization_type = 'user'::organization_type) AND (title IS NULL)) OR ((organization_type <> 'user'::organization_type) AND (title IS NOT NULL))"),
        sa.CheckConstraint("((organization_type = 'user'::organization_type) AND (user_id IS NOT NULL)) OR ((organization_type <> 'user'::organization_type) AND (user_id IS NULL))"),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE', onupdate='RESTRICT')
    )
    
    # Add indexes for organization
    op.create_index('organization_path_key', 'organization', ['organization_type', 'path'], unique=True)
    op.create_index('organization_number_key', 'organization', ['organization_type', 'number'], unique=True)
    op.create_index('ix_organization_organization_type', 'organization', ['organization_type'])
    op.create_index('ix_organization_path', 'organization', ['path'])
    
    # Execution Backend
    op.create_table('execution_backend',
        sa.Column('id', postgresql.UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column('version', sa.BigInteger, server_default=sa.text("0")),
        sa.Column('created_at', sa.DateTime(True), nullable=False, server_default=sa.text("now()")),
        sa.Column('updated_at', sa.DateTime(True), nullable=False, server_default=sa.text("now()")),
        sa.Column('created_by', postgresql.UUID),
        sa.Column('updated_by', postgresql.UUID),
        sa.Column('properties', postgresql.JSONB),
        sa.Column('type', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False, unique=True),
        sa.CheckConstraint("(slug)::text ~* '^[A-Za-z0-9_-]+$'::text"),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['user.id'], ondelete='SET NULL')
    )
    
    # Continue with remaining tables...
    # (I'll add the rest in the next part due to length)


def downgrade() -> None:
    # Drop all tables
    op.drop_table('execution_backend')
    op.drop_table('organization')
    op.drop_table('user')
    op.drop_table('role')
    op.drop_table('group')
    op.drop_table('course_role')
    op.drop_table('course_content_kind')
    
    # Drop sequences
    op.execute("DROP SEQUENCE IF EXISTS user_unique_fs_number_seq;")
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS ctutor_on_user_update CASCADE;")
    op.execute("DROP FUNCTION IF EXISTS ctutor_valid_slug CASCADE;")
    
    # Drop types
    op.execute("DROP TYPE IF EXISTS ctutor_color CASCADE;")
    op.execute("DROP TYPE IF EXISTS ctutor_group_type CASCADE;")
    op.execute("DROP TYPE IF EXISTS user_type CASCADE;")
    op.execute("DROP TYPE IF EXISTS organization_type CASCADE;")
    
    # Drop extensions
    op.execute("DROP EXTENSION IF EXISTS pgcrypto CASCADE;")
    op.execute("DROP EXTENSION IF EXISTS ltree CASCADE;")
    op.execute("DROP EXTENSION IF EXISTS \"uuid-ossp\" CASCADE;")