"""
SQLAlchemy model for ExampleDeployment.

This model tracks where examples are deployed in student-template repositories.
It serves as the source of truth for what content exists in student repositories,
independent of CourseContent lifecycle.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, text, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy_utils.types.ltree import LtreeType

from .base import Base


class ExampleDeployment(Base):
    """
    Tracks deployment of examples to student-template repositories.
    
    This is the authoritative record of what examples are deployed where,
    surviving CourseContent deletion and maintaining full deployment history.
    """
    
    __tablename__ = "example_deployment"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    
    # Example reference (what was deployed)
    example_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("example.id", ondelete="RESTRICT"),  # Prevent example deletion if deployed
        nullable=False,
        comment="The example that was deployed"
    )
    example_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("example_version.id", ondelete="RESTRICT"),  # Prevent version deletion if deployed
        nullable=False,
        comment="Specific version of the example that was deployed"
    )
    
    # Course reference (where it was deployed)
    course_id = Column(
        UUID(as_uuid=True),
        ForeignKey("course.id", ondelete="CASCADE"),  # Remove deployments if course deleted
        nullable=False,
        comment="Course this deployment belongs to"
    )
    
    # Optional CourseContent reference (can be null if CourseContent deleted)
    course_content_id = Column(
        UUID(as_uuid=True),
        ForeignKey("course_content.id", ondelete="SET NULL"),  # Preserve deployment if content deleted
        nullable=True,
        comment="CourseContent that triggered this deployment (may be deleted)"
    )
    
    # Deployment location
    deployment_path = Column(
        LtreeType,
        nullable=False,
        comment="Path in student-template repository (e.g., 'week1.assignment1')"
    )
    
    # Deployment metadata
    deployed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="When this deployment occurred"
    )
    deployed_by = Column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who triggered the deployment"
    )
    
    # Status tracking
    status = Column(
        String(32),
        nullable=False,
        default="active",
        comment="Status: active, replaced, removed, failed"
    )
    removed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this deployment was removed/replaced"
    )
    removed_by = Column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who removed this deployment"
    )
    removal_reason = Column(
        String(255),
        nullable=True,
        comment="Reason for removal: replaced, content_deleted, manual_removal, etc."
    )
    
    # Git tracking
    commit_hash = Column(
        String(40),
        nullable=True,
        comment="Git commit hash of this deployment in student-template"
    )
    
    # Additional metadata
    properties = Column(
        JSONB,
        nullable=True,
        comment="Additional deployment metadata (customizations, notes, etc.)"
    )
    
    # Relationships
    example = relationship("Example", back_populates="deployments")
    example_version = relationship("ExampleVersion", back_populates="deployments")
    course = relationship("Course", back_populates="example_deployments")
    course_content = relationship("CourseContent", back_populates="example_deployments")
    deployed_by_user = relationship("User", foreign_keys=[deployed_by])
    removed_by_user = relationship("User", foreign_keys=[removed_by])
    
    # Indexes and constraints
    __table_args__ = (
        # Only one active deployment per path per course
        Index(
            'ix_unique_active_deployment',
            'course_id',
            'deployment_path',
            unique=True,
            postgresql_where=(text("status = 'active'"))
        ),
        
        # Ensure path format
        CheckConstraint(
            "deployment_path::text ~ '^[a-z0-9_]+(\\.[a-z0-9_]+)*$'",
            name='check_deployment_path_format'
        ),
        
        # Status validation
        CheckConstraint(
            "status IN ('active', 'replaced', 'removed', 'failed')",
            name='check_deployment_status'
        ),
        
        # Removal fields consistency
        CheckConstraint(
            "(status IN ('removed', 'replaced') AND removed_at IS NOT NULL) OR "
            "(status IN ('active', 'failed') AND removed_at IS NULL)",
            name='check_removal_consistency'
        ),
    )
    
    def __repr__(self):
        return f"<ExampleDeployment(course_id={self.course_id}, path={self.deployment_path}, status={self.status})>"