"""Add ExampleDeployment table

Revision ID: add_example_deployment
Revises: add_deployment_fields_to_course_content
Create Date: 2024-08-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy_utils import LtreeType

# revision identifiers, used by Alembic.
revision = 'add_example_deployment'
down_revision = 'add_deployment_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the example_deployment table
    op.create_table('example_deployment',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column('example_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('example_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('course_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('course_content_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deployment_path', LtreeType(), nullable=False),
        sa.Column('deployed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deployed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(32), nullable=False, server_default='active'),
        sa.Column('removed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('removed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('removal_reason', sa.String(255), nullable=True),
        sa.Column('commit_hash', sa.String(40), nullable=True),
        sa.Column('properties', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['example_id'], ['example.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['example_version_id'], ['example_version.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['course_id'], ['course.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['course_content_id'], ['course_content.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deployed_by'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['removed_by'], ['user.id'], ondelete='SET NULL'),
        
        sa.CheckConstraint(
            "deployment_path::text ~ '^[a-z0-9_]+(\\.[a-z0-9_]+)*$'",
            name='check_deployment_path_format'
        ),
        sa.CheckConstraint(
            "status IN ('active', 'replaced', 'removed', 'failed')",
            name='check_deployment_status'
        ),
        sa.CheckConstraint(
            "(status IN ('removed', 'replaced') AND removed_at IS NOT NULL) OR "
            "(status IN ('active', 'failed') AND removed_at IS NULL)",
            name='check_removal_consistency'
        ),
    )
    
    # Create unique index for active deployments
    op.create_index(
        'ix_unique_active_deployment',
        'example_deployment',
        ['course_id', 'deployment_path'],
        unique=True,
        postgresql_where=sa.text("status = 'active'")
    )
    
    # Also make version_identifier nullable in course_content
    op.alter_column('course_content', 'version_identifier',
                    existing_type=sa.String(2048),
                    nullable=True)


def downgrade() -> None:
    # Make version_identifier required again
    op.alter_column('course_content', 'version_identifier',
                    existing_type=sa.String(2048),
                    nullable=False)
    
    # Drop the indexes first
    op.drop_index('ix_unique_active_deployment', table_name='example_deployment')
    
    # Drop the table
    op.drop_table('example_deployment')