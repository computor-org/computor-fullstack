"""Add source_type to ExampleRepository

Revision ID: add_example_repository_source_type
Revises: course_content_improvements
Create Date: 2025-07-29 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_example_repository_source_type'
down_revision = 'course_content_improvements'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add source_type column with default 'git' for existing repositories
    op.add_column('example_repository', 
        sa.Column('source_type', sa.String(length=20), nullable=False, server_default='git',
                  comment='Type of repository source: git, minio, github, etc.')
    )
    
    # Add check constraint for source_type values
    op.create_check_constraint(
        'check_source_type',
        'example_repository',
        "source_type IN ('git', 'minio', 'github', 's3', 'gitlab')"
    )
    
    # Update column comments to reflect new flexibility
    op.alter_column('example_repository', 'source_url',
                    comment='Repository URL (Git URL, MinIO path, etc.)',
                    existing_type=sa.Text(),
                    existing_nullable=False)
    
    op.alter_column('example_repository', 'access_token',
                    comment='Encrypted access credentials (Git token, MinIO credentials JSON, etc.)',
                    existing_type=sa.Text(),
                    existing_nullable=True)
    
    op.alter_column('example_repository', 'default_branch',
                    comment='Default branch/version to sync from',
                    existing_type=sa.String(100),
                    existing_nullable=False)


def downgrade() -> None:
    # Drop the check constraint
    op.drop_constraint('check_source_type', 'example_repository')
    
    # Revert column comments
    op.alter_column('example_repository', 'default_branch',
                    comment='Default branch to sync from',
                    existing_type=sa.String(100),
                    existing_nullable=False)
    
    op.alter_column('example_repository', 'access_token',
                    comment='Encrypted token for accessing private repositories',
                    existing_type=sa.Text(),
                    existing_nullable=True)
    
    op.alter_column('example_repository', 'source_url',
                    comment='Git repository URL',
                    existing_type=sa.Text(),
                    existing_nullable=False)
    
    # Drop the source_type column
    op.drop_column('example_repository', 'source_type')