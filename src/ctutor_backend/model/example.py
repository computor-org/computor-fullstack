"""
SQLAlchemy model for Example.

This model represents individual examples/assignments within an ExampleRepository.
Each example is stored in its own directory with a flat structure.
"""

from sqlalchemy import Column, String, Text, Boolean, DateTime, ARRAY, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import CheckConstraint, UniqueConstraint

from .base import Base


class ExampleRepository(Base):
    """
    Repository containing examples/assignments in flat directory structure.
    
    Each repository contains multiple examples, each in its own directory.
    The repository can be public, private, or restricted to specific organizations.
    """
    
    __tablename__ = "example_repositories"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    
    # Repository information
    name = Column(String(255), nullable=False, comment="Human-readable name of the repository")
    description = Column(Text, comment="Description of the repository and its contents")
    
    # Git repository information
    source_url = Column(Text, nullable=False, unique=True, comment="Git repository URL")
    access_token = Column(Text, comment="Encrypted token for accessing private repositories")
    default_branch = Column(String(100), nullable=False, default="main", comment="Default branch to sync from")
    
    # Access control
    visibility = Column(
        String(20), 
        nullable=False, 
        default="private",
        comment="Repository visibility: public, private, or restricted"
    )
    organization_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("organizations.id"),
        comment="Organization that owns this repository"
    )
    
    # Tracking
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), comment="User who created this repository")
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), comment="User who last updated this repository")
    
    # Relationships
    examples = relationship("Example", back_populates="repository", cascade="all, delete-orphan")
    organization = relationship("Organization", back_populates="example_repositories")
    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "visibility IN ('public', 'private', 'restricted')",
            name="check_visibility"
        ),
    )
    
    def __repr__(self):
        return f"<ExampleRepository(id={self.id}, name='{self.name}')>"
    
    @property
    def is_public(self) -> bool:
        """Check if repository is publicly accessible."""
        return self.visibility == "public"
    
    @property
    def is_private(self) -> bool:
        """Check if repository is private."""
        return self.visibility == "private"
    
    @property
    def is_restricted(self) -> bool:
        """Check if repository is restricted to specific organizations."""
        return self.visibility == "restricted"
    
    @property
    def needs_token(self) -> bool:
        """Check if repository requires access token."""
        return not self.is_public and self.access_token is not None


class Example(Base):
    """
    Individual example/assignment within an ExampleRepository.
    
    Each example corresponds to a directory in the repository's flat structure.
    Contains educational metadata and file structure information.
    """
    
    __tablename__ = "examples"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    
    # Repository relationship
    example_repository_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("example_repositories.id", ondelete="CASCADE"), 
        nullable=False,
        comment="Reference to the repository containing this example"
    )
    
    # Location within repository (flat structure)
    directory = Column(
        String(255), 
        nullable=False,
        comment="Name of the directory containing this example (e.g., 'hello-world')"
    )
    
    # Example metadata
    title = Column(String(255), nullable=False, comment="Human-readable title of the example")
    description = Column(Text, comment="Detailed description of the example")
    subject = Column(String(50), comment="Primary programming language (e.g., 'python', 'java')")
    
    # Organization and categorization
    category = Column(String(100), comment="Category for grouping examples")
    tags = Column(ARRAY(String), nullable=False, default=[], comment="Tags for searching and filtering")
    
    version_identifier = Column(String(64), comment="Version Identifier (e.g. hash) of example directory contents for change detection")
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True, comment="Whether the example is active")
    
    # Tracking
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), comment="User who created this example record")
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), comment="User who last updated this example record")
    
    # Relationships
    repository = relationship("ExampleRepository", back_populates="examples")
    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    
    # Constraints
    __table_args__ = (
        # Unique constraint: one example per directory per repository
        UniqueConstraint("example_repository_id", "directory", name="unique_example_per_directory"),
        
        # Check constraints
        CheckConstraint(
            "directory ~ '^[a-zA-Z0-9_-]+$'",
            name="check_directory_format"
        ),
    )
    
    def __repr__(self):
        return f"<Example(id={self.id}, title='{self.title}', directory='{self.directory}')>"
    
    @property
    def full_path(self) -> str:
        """Get the full path within the repository."""
        return self.directory
