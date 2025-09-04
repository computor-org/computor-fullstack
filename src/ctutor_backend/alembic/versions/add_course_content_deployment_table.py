"""Add course_content_deployment and deployment_history tables

Revision ID: add_course_content_deployment
Revises: add_example_version_id
Create Date: 2024-01-15

This migration:
1. Creates course_content_deployment table for tracking deployments
2. Creates deployment_history table for audit logging
3. Migrates existing deployment data from course_content table
4. Adds trigger to validate only submittable content has deployments
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_course_content_deployment'
down_revision = 'add_example_version_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create new deployment tables and migrate existing data.
    """
    # Create course_content_deployment table
    op.create_table('course_content_deployment',
        sa.Column('id', postgresql.UUID, server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column('course_content_id', postgresql.UUID, nullable=False, comment='The course content (assignment) this deployment is for'),
        sa.Column('example_version_id', postgresql.UUID, nullable=True, comment='The specific example version that is/was deployed'),
        sa.Column('deployment_status', sa.String(32), nullable=False, server_default='pending', 
                  comment='Status: pending, deploying, deployed, failed, unassigned'),
        sa.Column('deployment_message', sa.Text, nullable=True, comment='Additional message about deployment (e.g., error details)'),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(),
                  comment='When the example was assigned to this content'),
        sa.Column('deployed_at', sa.DateTime(timezone=True), nullable=True, comment='When the deployment was successfully completed'),
        sa.Column('last_attempt_at', sa.DateTime(timezone=True), nullable=True, comment='When the last deployment attempt was made'),
        sa.Column('deployment_path', sa.Text, nullable=True, comment='Path in the student-template repository where deployed'),
        sa.Column('deployment_metadata', postgresql.JSONB, nullable=True, server_default=sa.text("'{}'::jsonb"),
                  comment='Additional deployment data (workflow IDs, file lists, etc.)'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID, nullable=True),
        sa.Column('updated_by', postgresql.UUID, nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['course_content_id'], ['course_content.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['example_version_id'], ['example_version.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['user.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('course_content_id', name='uq_deployment_per_content')
    )
    
    # Create indexes for course_content_deployment
    op.create_index('idx_deployment_status', 'course_content_deployment', ['deployment_status'])
    op.create_index('idx_deployment_deployed_at', 'course_content_deployment', ['deployed_at'])
    op.create_index('idx_deployment_example_version', 'course_content_deployment', ['example_version_id'])
    
    # Create deployment_history table
    op.create_table('deployment_history',
        sa.Column('id', postgresql.UUID, server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column('deployment_id', postgresql.UUID, nullable=False, 
                  comment='The deployment this history entry belongs to'),
        sa.Column('action', sa.String(32), nullable=False,
                  comment='Action type: assigned, reassigned, deployed, failed, unassigned, updated'),
        sa.Column('action_details', sa.Text, nullable=True, comment='Detailed description of the action'),
        sa.Column('example_version_id', postgresql.UUID, nullable=True,
                  comment='The example version involved in this action'),
        sa.Column('previous_example_version_id', postgresql.UUID, nullable=True,
                  comment='Previous example version (for reassignments)'),
        sa.Column('metadata', postgresql.JSONB, nullable=True, server_default=sa.text("'{}'::jsonb"),
                  comment='Additional metadata about the action'),
        sa.Column('workflow_id', sa.String(255), nullable=True,
                  comment='Temporal workflow ID if action was triggered by workflow'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID, nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['deployment_id'], ['course_content_deployment.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['example_version_id'], ['example_version.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['previous_example_version_id'], ['example_version.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ondelete='SET NULL')
    )
    
    # Create indexes for deployment_history
    op.create_index('idx_history_deployment_id', 'deployment_history', ['deployment_id'])
    op.create_index('idx_history_action', 'deployment_history', ['action'])
    op.create_index('idx_history_created_at', 'deployment_history', ['created_at'])
    op.create_index('idx_history_workflow_id', 'deployment_history', ['workflow_id'])
    
    # Migrate existing deployment data from course_content to course_content_deployment
    connection = op.get_bind()
    
    # Only migrate data for submittable content (assignments)
    connection.execute(sa.text("""
        INSERT INTO course_content_deployment (
            course_content_id,
            example_version_id,
            deployment_status,
            deployed_at,
            deployment_metadata,
            created_at,
            updated_at,
            created_by,
            updated_by
        )
        SELECT 
            cc.id as course_content_id,
            cc.example_version_id,
            COALESCE(cc.deployment_status, 'pending') as deployment_status,
            cc.deployed_at,
            CASE 
                WHEN cc.properties IS NOT NULL AND cc.properties ? 'deployment_history'
                THEN jsonb_build_object('migrated_properties', cc.properties->'deployment_history')
                ELSE '{}'::jsonb
            END as deployment_metadata,
            COALESCE(cc.created_at, NOW()) as created_at,
            COALESCE(cc.updated_at, NOW()) as updated_at,
            cc.created_by,
            cc.updated_by
        FROM course_content cc
        JOIN course_content_type cct ON cc.course_content_type_id = cct.id
        JOIN course_content_kind cck ON cct.course_content_kind_id = cck.id
        WHERE cck.submittable = true
        AND cc.example_version_id IS NOT NULL
    """))
    
    # Create initial history entries for migrated deployments
    connection.execute(sa.text("""
        INSERT INTO deployment_history (
            deployment_id,
            action,
            action_details,
            example_version_id,
            created_at
        )
        SELECT 
            cd.id,
            'migrated',
            'Migrated from course_content table during schema refactoring',
            cd.example_version_id,
            NOW()
        FROM course_content_deployment cd
    """))
    
    # Create function to validate deployments only for submittable content
    op.execute("""
        CREATE OR REPLACE FUNCTION validate_deployment_submittable()
        RETURNS TRIGGER AS $$
        DECLARE
            v_submittable BOOLEAN;
        BEGIN
            -- Check if the course content is submittable
            SELECT cck.submittable INTO v_submittable
            FROM course_content cc
            JOIN course_content_type cct ON cc.course_content_type_id = cct.id
            JOIN course_content_kind cck ON cct.course_content_kind_id = cck.id
            WHERE cc.id = NEW.course_content_id;
            
            IF v_submittable IS NULL THEN
                RAISE EXCEPTION 'Course content % not found', NEW.course_content_id;
            ELSIF NOT v_submittable THEN
                RAISE EXCEPTION 'Cannot create deployment for non-submittable content %', NEW.course_content_id;
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger to validate deployments
    op.execute("""
        CREATE TRIGGER trg_validate_deployment_submittable
        BEFORE INSERT ON course_content_deployment
        FOR EACH ROW
        EXECUTE FUNCTION validate_deployment_submittable();
    """)
    
    # Add comment to course_content columns that are being deprecated
    op.execute("""
        COMMENT ON COLUMN course_content.deployment_status IS 
        'DEPRECATED: Use course_content_deployment.deployment_status instead';
        
        COMMENT ON COLUMN course_content.deployed_at IS 
        'DEPRECATED: Use course_content_deployment.deployed_at instead';
        
        COMMENT ON COLUMN course_content.example_id IS 
        'DEPRECATED: Use example_version.example_id via course_content_deployment.example_version_id';
        
        COMMENT ON COLUMN course_content.example_version_id IS 
        'DEPRECATED: Use course_content_deployment.example_version_id instead';
    """)


def downgrade() -> None:
    """
    Restore deployment data to course_content and drop new tables.
    """
    connection = op.get_bind()
    
    # Restore deployment data to course_content
    connection.execute(sa.text("""
        UPDATE course_content cc
        SET 
            deployment_status = cd.deployment_status,
            deployed_at = cd.deployed_at
        FROM course_content_deployment cd
        WHERE cc.id = cd.course_content_id
    """))
    
    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS trg_validate_deployment_submittable ON course_content_deployment CASCADE")
    op.execute("DROP FUNCTION IF EXISTS validate_deployment_submittable() CASCADE")
    
    # Drop indexes
    op.drop_index('idx_history_workflow_id', 'deployment_history')
    op.drop_index('idx_history_created_at', 'deployment_history')
    op.drop_index('idx_history_action', 'deployment_history')
    op.drop_index('idx_history_deployment_id', 'deployment_history')
    op.drop_index('idx_deployment_example_version', 'course_content_deployment')
    op.drop_index('idx_deployment_deployed_at', 'course_content_deployment')
    op.drop_index('idx_deployment_status', 'course_content_deployment')
    
    # Drop tables
    op.drop_table('deployment_history')
    op.drop_table('course_content_deployment')
    
    # Remove comments from course_content columns
    op.execute("""
        COMMENT ON COLUMN course_content.deployment_status IS NULL;
        COMMENT ON COLUMN course_content.deployed_at IS NULL;
        COMMENT ON COLUMN course_content.example_id IS NULL;
        COMMENT ON COLUMN course_content.example_version_id IS NULL;
    """)