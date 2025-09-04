from typing import List, TYPE_CHECKING
from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, Column, DateTime, 
    Float, ForeignKey, ForeignKeyConstraint, Index, 
    Integer, String, text, select
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship, column_property, Mapped
try:
    from ..custom_types import LtreeType
except ImportError:
    # Fallback for Alembic context
    from ctutor_backend.custom_types import LtreeType

from .base import Base

if TYPE_CHECKING:
    from .result import Result
    from .example import ExampleVersion


class CourseContentKind(Base):
    __tablename__ = 'course_content_kind'

    id = Column(String(255), primary_key=True)
    title = Column(String(255))
    description = Column(String(4096))
    has_ascendants = Column(Boolean, nullable=False)
    has_descendants = Column(Boolean, nullable=False)
    submittable = Column(Boolean, nullable=False)

    # Relationships
    course_content_types = relationship('CourseContentType', back_populates='course_content_kind')


class CourseRole(Base):
    __tablename__ = 'course_role'
    __table_args__ = (
        CheckConstraint("(NOT builtin) OR ((id)::text ~ '^_'::text)"),
        CheckConstraint('(builtin AND ctutor_valid_slug(SUBSTRING(id FROM 2))) OR ((NOT builtin) AND ctutor_valid_slug((id)::text))')
    )

    id = Column(String(255), primary_key=True)
    title = Column(String(255))
    description = Column(String(4096))
    builtin = Column(Boolean, nullable=False, server_default=text("false"))

    # Relationships
    course_members = relationship('CourseMember', back_populates='course_role')


class CourseFamily(Base):
    __tablename__ = 'course_family'
    __table_args__ = (
        Index('course_family_path_key', 'organization_id', 'path', unique=True),
    )

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    updated_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    properties = Column(JSONB)
    title = Column(String(255))
    description = Column(String(4096))
    path = Column(LtreeType, nullable=False)
    organization_id = Column(ForeignKey('organization.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)

    # Relationships
    created_by_user = relationship('User', foreign_keys=[created_by])
    updated_by_user = relationship('User', foreign_keys=[updated_by])
    organization = relationship('Organization', back_populates='course_families')
    courses = relationship('Course', back_populates='course_family')


class Course(Base):
    __tablename__ = 'course'
    __table_args__ = (
        Index('course_path_key', 'course_family_id', 'path', unique=True),
    )

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    updated_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    properties = Column(JSONB)
    title = Column(String(255))
    description = Column(String(4096))
    path = Column(LtreeType, nullable=False)
    course_family_id = Column(ForeignKey('course_family.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    organization_id = Column(ForeignKey('organization.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)

    # Relationships
    course_family = relationship('CourseFamily', back_populates='courses')
    created_by_user = relationship('User', foreign_keys=[created_by])
    updated_by_user = relationship('User', foreign_keys=[updated_by])
    organization = relationship('Organization', back_populates='courses')
    course_members = relationship("CourseMember", back_populates="course", uselist=True, lazy="select")
    course_content_types = relationship("CourseContentType", back_populates="course", uselist=True, lazy="select")
    course_groups = relationship("CourseGroup", back_populates="course", uselist=True, lazy="select")
    course_execution_backends = relationship("CourseExecutionBackend", back_populates="course", uselist=True)
    course_contents = relationship("CourseContent", foreign_keys="CourseContent.course_id", back_populates="course", uselist=True)
    course_submission_groups = relationship("CourseSubmissionGroup", back_populates="course", uselist=True)
    messages = relationship("Message", back_populates="course", uselist=True)


class CourseContentType(Base):
    __tablename__ = 'course_content_type'
    __table_args__ = (
        CheckConstraint("(slug)::text ~* '^[A-Za-z0-9_-]+$'::text"),
        Index('course_content_type_course_id_key', 'id', 'course_id', unique=True),
        Index('course_content_type_slug_key', 'slug', 'course_id', 'course_content_kind_id', unique=True)
    )

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    updated_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    properties = Column(JSONB)
    title = Column(String(255))
    description = Column(String(4096))
    slug = Column(String(255), nullable=False)
    color = Column(String(255))
    course_content_kind_id = Column(ForeignKey('course_content_kind.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    course_id = Column(ForeignKey('course.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)

    # Relationships
    course_contents = relationship("CourseContent", back_populates="course_content_type", foreign_keys="CourseContent.course_content_type_id", uselist=True, lazy="select")
    course_content_kind = relationship('CourseContentKind', back_populates='course_content_types')
    course = relationship("Course", back_populates="course_content_types", lazy="select")
    created_by_user = relationship('User', foreign_keys=[created_by])
    updated_by_user = relationship('User', foreign_keys=[updated_by])
    results = relationship('Result', back_populates='course_content_type')


class CourseExecutionBackend(Base):
    __tablename__ = 'course_execution_backend'

    execution_backend_id = Column(ForeignKey('execution_backend.id', ondelete='CASCADE', onupdate='RESTRICT'), primary_key=True, nullable=False)
    course_id = Column(ForeignKey('course.id', ondelete='CASCADE', onupdate='RESTRICT'), primary_key=True, nullable=False)
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(UUID)
    updated_by = Column(UUID)
    properties = Column(JSONB)

    # Relationships
    course = relationship('Course', back_populates='course_execution_backends')
    execution_backend = relationship('ExecutionBackend', back_populates='course_execution_backends')


class CourseGroup(Base):
    __tablename__ = 'course_group'
    __table_args__ = (
        Index('course_group_course_id_key', 'course_id', 'id', unique=True),
        Index('course_group_title_key', 'course_id', 'title', unique=True)
    )

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    updated_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    properties = Column(JSONB)
    title = Column(String(255))
    description = Column(String(4096))
    course_id = Column(ForeignKey('course.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)

    # Relationships
    course = relationship('Course', back_populates='course_groups')
    created_by_user = relationship('User', foreign_keys=[created_by])
    updated_by_user = relationship('User', foreign_keys=[updated_by])
    course_members = relationship('CourseMember', back_populates='course_group', foreign_keys='CourseMember.course_group_id')


class CourseContent(Base):
    __tablename__ = 'course_content'
    __table_args__ = (
        ForeignKeyConstraint(['course_id', 'course_content_type_id'], 
                           ['course_content_type.course_id', 'course_content_type.id'], 
                           ondelete='RESTRICT', onupdate='RESTRICT'),
        Index('course_content_path_key', 'course_id', 'path', unique=True),
        CheckConstraint("path::text ~ '^[a-z0-9_]+(\\.[a-z0-9_]+)*$'", name='course_content_path_format')
        # Note: Example-submittable validation is enforced by database trigger
        # validate_course_content_example_submittable_trigger
    )

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    updated_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    properties = Column(JSONB)
    archived_at = Column(DateTime(True))
    title = Column(String(255))
    description = Column(String(4096))
    path = Column(LtreeType, nullable=False)
    course_id = Column(ForeignKey('course.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    course_content_type_id = Column(ForeignKey('course_content_type.id', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False)
    position = Column(Float(53), nullable=False)
    max_group_size = Column(Integer, nullable=True)
    max_test_runs = Column(Integer)
    max_submissions = Column(Integer)
    execution_backend_id = Column(ForeignKey('execution_backend.id', ondelete='CASCADE', onupdate='RESTRICT'))
    
    # Example version tracking (DEPRECATED - will be removed, use CourseContentDeployment.example_version_id)
    example_version_id = Column(UUID, ForeignKey('example_version.id', ondelete='SET NULL'), nullable=True)
    

    # Relationships
    course_content_type = relationship("CourseContentType", foreign_keys=[course_content_type_id], back_populates="course_contents", lazy="select")
    course = relationship('Course', foreign_keys=[course_id], back_populates='course_contents')
    created_by_user = relationship('User', foreign_keys=[created_by])
    updated_by_user = relationship('User', foreign_keys=[updated_by])
    execution_backend = relationship('ExecutionBackend', back_populates='course_contents')
    results: Mapped[List["Result"]] = relationship('Result', back_populates="course_content", uselist=True, cascade='all,delete')
    course_submission_groups = relationship('CourseSubmissionGroup', back_populates='course_content')
    # Removed: course_submission_group_members - relationship removed as course_content_id was removed from CourseSubmissionGroupMember
    
    # Example relationships (via example_version_id - DEPRECATED)
    example_version = relationship('ExampleVersion', foreign_keys=[example_version_id])
    
    # Deployment tracking - One-to-one relationship with CourseContentDeployment
    deployment = relationship('CourseContentDeployment', back_populates='course_content', uselist=False)

    # Column property for course_content_kind_id
    course_content_kind_id = column_property(
        select(CourseContentKind.id)
        .where(CourseContentKind.id == CourseContentType.course_content_kind_id, 
               CourseContentType.id == course_content_type_id)
        .scalar_subquery()
    )
    
    # Column property for is_submittable - derived from CourseContentKind.submittable
    is_submittable = column_property(
        select(CourseContentKind.submittable)
        .where(
            CourseContentKind.id == CourseContentType.course_content_kind_id,
            CourseContentType.id == course_content_type_id
        )
        .scalar_subquery()
    )
    
    # Column property for has_deployment - check if deployment exists
    @property 
    def has_deployment(self):
        """Check if this course content has a deployment."""
        # Only submittable content can have deployments
        if not self.is_submittable:
            return False
        return self.deployment is not None
    
    # Column property for deployment_status - get status from deployment if exists
    @property
    def deployment_status(self):
        """Get deployment status if deployment exists."""
        # Only submittable content can have deployments
        if not self.is_submittable:
            return None
        if self.deployment:
            return self.deployment.deployment_status
        return None


class CourseMember(Base):
    __tablename__ = 'course_member'
    __table_args__ = (
        CheckConstraint("""
            CASE
                WHEN ((course_role_id)::text = '_student'::text) THEN (course_group_id IS NOT NULL)
                ELSE true
            END"""),
        ForeignKeyConstraint(['course_id', 'course_group_id'], 
                           ['course_group.course_id', 'course_group.id'], 
                           ondelete='RESTRICT', onupdate='RESTRICT'),
        Index('course_member_key', 'user_id', 'course_id', unique=True)
    )

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    updated_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    properties = Column(JSONB)
    user_id = Column(ForeignKey('user.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    course_id = Column(ForeignKey('course.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    course_group_id = Column(ForeignKey('course_group.id', ondelete='RESTRICT', onupdate='RESTRICT'))
    course_role_id = Column(ForeignKey('course_role.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)

    # Relationships
    course_group = relationship('CourseGroup', foreign_keys=[course_group_id], back_populates='course_members')
    course = relationship("Course", foreign_keys=[course_id], back_populates="course_members", lazy="select")
    course_role = relationship('CourseRole', back_populates='course_members')
    user = relationship("User", foreign_keys=[user_id], back_populates="course_members", uselist=False, lazy="select")
    created_by_user = relationship('User', foreign_keys=[created_by])
    updated_by_user = relationship('User', foreign_keys=[updated_by])
    comments_written = relationship("CourseMemberComment", foreign_keys="CourseMemberComment.transmitter_id", 
                                  back_populates="transmitter", uselist=True, lazy="select")
    comments_received = relationship("CourseMemberComment", foreign_keys="CourseMemberComment.course_member_id", 
                                   back_populates="course_member", uselist=True, lazy="select")
    submission_group_members = relationship('CourseSubmissionGroupMember', back_populates='course_member')
    results = relationship('Result', back_populates='course_member')
    messages_sent = relationship('Message', back_populates='transmitter')
    message_reads = relationship('MessageRead', back_populates='course_member')
    gradings_given = relationship('CourseSubmissionGroupGrading', back_populates='graded_by',
                                 foreign_keys='CourseSubmissionGroupGrading.graded_by_course_member_id')


class CourseSubmissionGroup(Base):
    __tablename__ = 'course_submission_group'

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    updated_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    properties = Column(JSONB)  # Should contain gitlab/git repository info
    # Removed: status and grading - moved to CourseSubmissionGroupGrading
    max_group_size = Column(Integer, nullable=False)
    max_test_runs = Column(Integer)
    max_submissions = Column(Integer)
    course_id = Column(ForeignKey('course.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    course_content_id = Column(ForeignKey('course_content.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)

    # Relationships
    course_content = relationship('CourseContent', back_populates='course_submission_groups')
    course = relationship('Course', back_populates='course_submission_groups')
    created_by_user = relationship('User', foreign_keys=[created_by])
    updated_by_user = relationship('User', foreign_keys=[updated_by])
    members = relationship("CourseSubmissionGroupMember", back_populates="group", uselist=True)
    results = relationship('Result', back_populates='course_submission_group')
    gradings = relationship('CourseSubmissionGroupGrading', back_populates='course_submission_group',
                           cascade='all, delete-orphan')


class CourseSubmissionGroupMember(Base):
    __tablename__ = 'course_submission_group_member'
    __table_args__ = (
        # Only keep the constraint that makes sense: unique member per submission group
        Index('course_submission_group_member_key', 'course_submission_group_id', 'course_member_id', unique=True),
    )

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    updated_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    properties = Column(JSONB)
    # Removed: grading - moved to CourseSubmissionGroupGrading
    course_id = Column(ForeignKey('course.id', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False, index=True)
    course_submission_group_id = Column(ForeignKey('course_submission_group.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    course_member_id = Column(ForeignKey('course_member.id', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False)
    # Removed: course_content_id - relationship is through CourseSubmissionGroup

    # Relationships
    # Removed relationship to course_content
    course = relationship('Course')
    course_member = relationship('CourseMember', back_populates='submission_group_members')
    group = relationship("CourseSubmissionGroup", back_populates="members", uselist=False)
    created_by_user = relationship('User', foreign_keys=[created_by])
    updated_by_user = relationship('User', foreign_keys=[updated_by])


class CourseSubmissionGroupGrading(Base):
    """
    Tracks grading information for course submission groups.
    
    This table records:
    - The actual grade (0.0 to 1.0)
    - The grading status
    - Who performed the grading (staff member/tutor/lecturer)
    - When the grading occurred
    """
    __tablename__ = 'course_submission_group_grading'
    __table_args__ = (
        # Ensure we can quickly find all gradings for a submission group
        Index('idx_grading_submission_group', 'course_submission_group_id'),
        # Ensure we can find all gradings by a specific grader
        Index('idx_grading_graded_by', 'graded_by_course_member_id'),
    )

    # Primary key and versioning
    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    version = Column(BigInteger, server_default=text("0"))
    
    # Timestamps
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    
    # Foreign keys
    course_submission_group_id = Column(
        ForeignKey('course_submission_group.id', ondelete='CASCADE', onupdate='RESTRICT'),
        nullable=False
    )
    graded_by_course_member_id = Column(
        ForeignKey('course_member.id', ondelete='RESTRICT', onupdate='RESTRICT'),
        nullable=False
    )
    
    # Grading data
    grading = Column(Float(53), nullable=False)  # Value between 0.0 and 1.0
    status = Column(String(50))  # 'corrected', 'correction_necessary', 'correction_possible', null, etc.
    
    # Relationships
    course_submission_group = relationship(
        'CourseSubmissionGroup',
        back_populates='gradings'
    )
    graded_by = relationship(
        'CourseMember',
        back_populates='gradings_given',
        foreign_keys=[graded_by_course_member_id]
    )
    
    def __repr__(self):
        return f"<CourseSubmissionGroupGrading(id={self.id}, grade={self.grading}, status={self.status})>"


class CourseMemberComment(Base):
    __tablename__ = 'course_member_comment'

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    updated_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    message = Column(String(4096), nullable=False)
    transmitter_id = Column(ForeignKey('course_member.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False, index=True)
    course_member_id = Column(ForeignKey('course_member.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False, index=True)

    # Relationships
    transmitter = relationship("CourseMember", foreign_keys=[transmitter_id], back_populates="comments_written", lazy="select")
    course_member = relationship("CourseMember", foreign_keys=[course_member_id], back_populates="comments_received", lazy="select")
    created_by_user = relationship('User', foreign_keys=[created_by])
    updated_by_user = relationship('User', foreign_keys=[updated_by])