"""Course Content Improvements

Revision ID: course_content_improvements
Revises: 6c2c37382ca7
Create Date: 2025-07-29 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'course_content_improvements'
down_revision = '6c2c37382ca7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add example integration columns to CourseContent
    op.add_column('course_content', sa.Column('example_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('course_content', sa.Column('example_version', sa.String(length=64), nullable=True))
    
    # Add foreign key constraints
    op.create_foreign_key('fk_course_content_example', 'course_content', 'example', ['example_id'], ['id'])
    
    # Add indexes for performance
    op.create_index('idx_course_content_example_id', 'course_content', ['example_id'])

    # 2. Create ExampleDependency table for managing dependencies
    op.create_table('example_dependency',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('example_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('depends_on_example_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dependency_type', sa.String(length=50), nullable=False),
        sa.Column('version_constraint', sa.String(length=100), nullable=True),
        sa.Column('relative_path', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['example_id'], ['example.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['depends_on_example_id'], ['example.id'], ondelete='CASCADE'),
        sa.CheckConstraint("dependency_type IN ('test', 'code', 'data', 'template')", name='check_dependency_type'),
        sa.UniqueConstraint('example_id', 'depends_on_example_id', 'dependency_type', name='unique_example_dependency')
    )
    
    # Add indexes for dependency lookups
    op.create_index('idx_example_dependency_example_id', 'example_dependency', ['example_id'])
    op.create_index('idx_example_dependency_depends_on', 'example_dependency', ['depends_on_example_id'])

    # 3. Add path format validation constraint
    op.create_check_constraint(
        'course_content_path_format',
        'course_content',
        "path::text ~ '^[a-z0-9_]+(\\.[a-z0-9_]+)*$'"
    )
    
    # 4. Create function to validate example assignment to submittable content only
    op.execute("""
        CREATE OR REPLACE FUNCTION validate_course_content_example_submittable()
        RETURNS TRIGGER AS $$
        DECLARE
            is_submittable BOOLEAN;
        BEGIN
            -- If no example is assigned, always allow
            IF NEW.example_id IS NULL AND NEW.example_version IS NULL THEN
                RETURN NEW;
            END IF;
            
            -- If example is assigned, check if content type is submittable
            SELECT cck.submittable INTO is_submittable
            FROM course_content_type cct
            JOIN course_content_kind cck ON cct.course_content_kind_id = cck.id
            WHERE cct.id = NEW.course_content_type_id;
            
            -- If content type is not submittable, reject the assignment
            IF NOT is_submittable THEN
                RAISE EXCEPTION 'Cannot assign example to non-submittable content type. Only assignments, quizzes, etc. can have examples.';
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger for example validation
    op.execute("""
        CREATE TRIGGER validate_course_content_example_submittable_trigger
        BEFORE INSERT OR UPDATE ON course_content
        FOR EACH ROW EXECUTE FUNCTION validate_course_content_example_submittable();
    """)

    # 5. Create tree structure validation function
    op.execute("""
        CREATE OR REPLACE FUNCTION validate_course_content_hierarchy()
        RETURNS TRIGGER AS $$
        DECLARE
            parent_allows_descendants BOOLEAN;
            current_allows_ascendants BOOLEAN;
            parent_path LTREE;
        BEGIN
            -- Skip validation for root level content (depth = 1)
            IF nlevel(NEW.path) <= 1 THEN
                RETURN NEW;
            END IF;
            
            -- Get parent path (remove last level)
            parent_path := subltree(NEW.path, 0, nlevel(NEW.path) - 1);
            
            -- Check if parent allows descendants
            SELECT cck.has_descendants INTO parent_allows_descendants
            FROM course_content cc
            JOIN course_content_type cct ON cc.course_content_type_id = cct.id
            JOIN course_content_kind cck ON cct.course_content_kind_id = cck.id
            WHERE cc.course_id = NEW.course_id 
            AND cc.path = parent_path;
            
            -- If parent doesn't exist or doesn't allow descendants, reject
            IF parent_allows_descendants IS NULL OR NOT parent_allows_descendants THEN
                RAISE EXCEPTION 'Parent content at path % does not allow descendants', parent_path;
            END IF;
            
            -- Check if current content type allows ascendants
            SELECT cck.has_ascendants INTO current_allows_ascendants
            FROM course_content_type cct
            JOIN course_content_kind cck ON cct.course_content_kind_id = cck.id
            WHERE cct.id = NEW.course_content_type_id;
            
            -- If current content doesn't allow ascendants, reject
            IF NOT current_allows_ascendants THEN
                RAISE EXCEPTION 'Content type % does not allow ascendants', 
                    (SELECT cck.id FROM course_content_type cct 
                     JOIN course_content_kind cck ON cct.course_content_kind_id = cck.id
                     WHERE cct.id = NEW.course_content_type_id);
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # 6. Create the trigger
    op.execute("""
        CREATE TRIGGER validate_course_content_hierarchy_trigger
        BEFORE INSERT OR UPDATE ON course_content
        FOR EACH ROW EXECUTE FUNCTION validate_course_content_hierarchy();
    """)

    # 7. Create management functions for easier operations
    op.execute("""
        CREATE OR REPLACE FUNCTION create_course_content(
            p_course_id UUID,
            p_content_type_slug VARCHAR,
            p_title VARCHAR,
            p_parent_path LTREE DEFAULT NULL,
            p_position FLOAT DEFAULT NULL,
            p_example_id UUID DEFAULT NULL,
            p_example_version VARCHAR DEFAULT NULL
        ) RETURNS UUID AS $$
        DECLARE
            v_content_type_id UUID;
            v_new_path LTREE;
            v_new_position FLOAT;
            v_content_id UUID;
            v_path_segment TEXT;
        BEGIN
            -- Get content type ID
            SELECT id INTO v_content_type_id
            FROM course_content_type 
            WHERE course_id = p_course_id AND slug = p_content_type_slug;
            
            IF v_content_type_id IS NULL THEN
                RAISE EXCEPTION 'Content type % not found for course %', p_content_type_slug, p_course_id;
            END IF;
            
            -- Generate path segment from title (sanitized)
            v_path_segment := lower(regexp_replace(p_title, '[^a-zA-Z0-9]', '_', 'g'));
            v_path_segment := regexp_replace(v_path_segment, '_+', '_', 'g');
            v_path_segment := trim(v_path_segment, '_');
            
            -- Generate full path
            IF p_parent_path IS NULL THEN
                v_new_path := text2ltree(v_path_segment);
            ELSE
                v_new_path := p_parent_path || text2ltree(v_path_segment);
            END IF;
            
            -- Generate position if not provided
            IF p_position IS NULL THEN
                SELECT COALESCE(MAX(position), 0) + 10 INTO v_new_position
                FROM course_content 
                WHERE course_id = p_course_id 
                AND (p_parent_path IS NULL AND nlevel(path) = 1 
                     OR p_parent_path IS NOT NULL AND path ~ (p_parent_path::text || '.*{1}')::lquery);
            ELSE
                v_new_position = p_position;
            END IF;
            
            -- Insert content
            INSERT INTO course_content (
                course_id, course_content_type_id, title, path, position,
                example_id, example_version, max_group_size, version_identifier
            ) VALUES (
                p_course_id, v_content_type_id, p_title, v_new_path, v_new_position,
                p_example_id, p_example_version, 1, 'initial'
            ) RETURNING id INTO v_content_id;
            
            RETURN v_content_id;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # 8. Create unified view for easier queries
    op.execute("""
        CREATE VIEW course_content_full AS
        SELECT 
            cc.id,
            cc.course_id,
            cc.title,
            cc.description,
            cc.path,
            cc.position,
            cc.max_group_size,
            cc.max_test_runs,
            cc.max_submissions,
            cc.version_identifier,
            cc.archived_at,
            cc.created_at,
            cc.updated_at,
            
            -- Content type information
            cct.slug as content_type_slug,
            cct.title as content_type_title,
            cct.color as content_type_color,
            
            -- Content kind information  
            cck.id as content_kind,
            cck.title as content_kind_title,
            cck.has_ascendants,
            cck.has_descendants,
            cck.submittable as kind_submittable,
            
            -- Example information
            cc.example_id,
            cc.example_version,
            e.title as example_title,
            e.directory as example_directory,
            e.subject as example_subject,
            e.tags as example_tags,
            er.name as example_repository_name,
            
            -- Hierarchy helpers
            nlevel(cc.path) as depth_level,
            CASE 
                WHEN nlevel(cc.path) > 1 THEN subltree(cc.path, 0, nlevel(cc.path) - 1)
                ELSE NULL
            END as parent_path
            
        FROM course_content cc
        JOIN course_content_type cct ON cc.course_content_type_id = cct.id
        JOIN course_content_kind cck ON cct.course_content_kind_id = cck.id
        LEFT JOIN example e ON cc.example_id = e.id
        LEFT JOIN example_repository er ON e.example_repository_id = er.id;
    """)

    # 9. Add standard CourseContentKind entries
    op.execute("""
        INSERT INTO course_content_kind (id, title, description, has_ascendants, has_descendants, submittable) VALUES
        ('unit', 'Unit', 'A thematic unit containing related content', false, true, false),
        ('folder', 'Folder', 'A folder for organizing content', true, true, false),
        ('assignment', 'Assignment', 'A submittable assignment', true, false, true),
        ('quiz', 'Quiz', 'An interactive quiz', true, false, true),
        ('reading', 'Reading', 'Reading material or resources', true, false, false)
        ON CONFLICT (id) DO NOTHING;
    """)


def downgrade() -> None:
    # Remove standard CourseContentKind entries (only if they have no dependencies)
    op.execute("""
        DELETE FROM course_content_kind 
        WHERE id IN ('unit', 'folder', 'assignment', 'quiz', 'reading')
        AND NOT EXISTS (
            SELECT 1 FROM course_content_type 
            WHERE course_content_kind_id = course_content_kind.id
        );
    """)
    
    # Drop the view
    op.execute("DROP VIEW IF EXISTS course_content_full;")
    
    # Drop the management function
    op.execute("DROP FUNCTION IF EXISTS create_course_content(UUID, VARCHAR, VARCHAR, LTREE, FLOAT, UUID, VARCHAR);")
    
    # Drop the trigger and function
    op.execute("DROP TRIGGER IF EXISTS validate_course_content_hierarchy_trigger ON course_content;")
    op.execute("DROP FUNCTION IF EXISTS validate_course_content_hierarchy();")
    
    # Drop triggers and functions
    op.execute("DROP TRIGGER IF EXISTS validate_course_content_example_submittable_trigger ON course_content;")
    op.execute("DROP FUNCTION IF EXISTS validate_course_content_example_submittable();")
    op.drop_constraint('course_content_path_format', 'course_content')
    
    # Drop ExampleDependency table
    op.drop_index('idx_example_dependency_depends_on', table_name='example_dependency')
    op.drop_index('idx_example_dependency_example_id', table_name='example_dependency')
    op.drop_table('example_dependency')
    
    # Drop CourseContent example columns
    op.drop_index('idx_course_content_example_id', table_name='course_content')
    op.drop_constraint('fk_course_content_example', 'course_content', type_='foreignkey')
    op.drop_column('course_content', 'example_version')
    op.drop_column('course_content', 'example_id')