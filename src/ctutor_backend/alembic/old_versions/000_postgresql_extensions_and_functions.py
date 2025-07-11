"""Create PostgreSQL extensions and utility functions

Revision ID: 000_extensions
Revises: 
Create Date: 2025-07-11

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '000_extensions'
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
            -- Check if the value matches the slug pattern
            RETURN value ~ '^[a-z0-9]+([_-][a-z0-9]+)*$';
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
    
    op.execute("""
        CREATE OR REPLACE FUNCTION ctutor_get_recursive_tree_ancestors(p ltree) 
        RETURNS SETOF ltree 
        LANGUAGE plpgsql
        AS $function$
        DECLARE
            current_path ltree;
            level integer;
        BEGIN
            IF p IS NULL THEN
                RETURN;
            END IF;
            
            level := nlevel(p);
            FOR i IN 1..level LOOP
                current_path := subpath(p, 0, i);
                RETURN NEXT current_path;
            END LOOP;
        END;
        $function$;
    """)
    
    op.execute("""
        CREATE OR REPLACE FUNCTION ctutor_encrypt_auth_token() 
        RETURNS trigger 
        LANGUAGE plpgsql
        AS $function$
        BEGIN
            IF NEW.auth_token IS NOT NULL AND NEW.auth_token != '' THEN
                NEW.auth_token = crypt(NEW.auth_token, gen_salt('bf'));
            END IF;
            RETURN NEW;
        END;
        $function$;
    """)
    
    # Create sequences
    op.execute("CREATE SEQUENCE IF NOT EXISTS user_unique_fs_number_seq;")
    
    # Create schema for interfaces if needed
    op.execute("CREATE SCHEMA IF NOT EXISTS interfaces;")


def downgrade() -> None:
    # Drop schema
    op.execute("DROP SCHEMA IF EXISTS interfaces CASCADE;")
    
    # Drop sequences
    op.execute("DROP SEQUENCE IF EXISTS user_unique_fs_number_seq;")
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS ctutor_encrypt_auth_token CASCADE;")
    op.execute("DROP FUNCTION IF EXISTS ctutor_get_recursive_tree_ancestors CASCADE;")
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