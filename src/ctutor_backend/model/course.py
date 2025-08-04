from typing import List, TYPE_CHECKING
from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, Column, DateTime, 
    Float, ForeignKey, ForeignKeyConstraint, Index, 
    Integer, String, text, select
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship, column_property, Mapped
from sqlalchemy_utils import LtreeType

from .base import Base

if TYPE_CHECKING:
    from .result import Result


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
    version_identifier = Column(String(2048))

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
    version_identifier = Column(String(2048), nullable=True)  # Made nullable - deprecated field
    position = Column(Float(53), nullable=False)
    max_group_size = Column(Integer, nullable=False)
    max_test_runs = Column(Integer)
    max_submissions = Column(Integer)
    execution_backend_id = Column(ForeignKey('execution_backend.id', ondelete='CASCADE', onupdate='RESTRICT'))
    
    # Example integration columns
    example_id = Column(UUID, ForeignKey('example.id'), nullable=True)
    example_version = Column(String(64), nullable=True)
    
    # Deployment tracking (basic status only)
    deployed_at = Column(DateTime(True), nullable=True)
    deployment_status = Column(String(32), server_default=text("'pending'"))  # pending, deploying, deployed, failed
    

    # Relationships
    course_content_type = relationship("CourseContentType", foreign_keys=[course_content_type_id], back_populates="course_contents", lazy="select")
    course = relationship('Course', foreign_keys=[course_id], back_populates='course_contents')
    created_by_user = relationship('User', foreign_keys=[created_by])
    updated_by_user = relationship('User', foreign_keys=[updated_by])
    execution_backend = relationship('ExecutionBackend', back_populates='course_contents')
    results: Mapped[List["Result"]] = relationship('Result', back_populates="course_content", uselist=True, cascade='all,delete')
    course_submission_groups = relationship('CourseSubmissionGroup', back_populates='course_content')
    course_submission_group_members = relationship('CourseSubmissionGroupMember', back_populates='course_content')
    
    # Example relationships
    example = relationship('Example', foreign_keys=[example_id], back_populates='course_contents')
    
    # Deployment tracking

    # Column property for course_content_kind_id
    course_content_kind_id = column_property(
        select(CourseContentKind.id)
        .where(CourseContentKind.id == CourseContentType.course_content_kind_id, 
               CourseContentType.id == course_content_type_id)
        .scalar_subquery()
    )


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


class CourseSubmissionGroup(Base):
    __tablename__ = 'course_submission_group'

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    updated_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    properties = Column(JSONB)
    status = Column(String(2048))
    grading = Column(Float(53))
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


class CourseSubmissionGroupMember(Base):
    __tablename__ = 'course_submission_group_member'
    __table_args__ = (
        Index('course_submission_group_course_content_key', 'course_member_id', 'course_content_id', unique=True),
        Index('course_submission_group_member_key', 'course_submission_group_id', 'course_member_id', unique=True)
    )

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    updated_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    properties = Column(JSONB)
    grading = Column(Float(53))
    course_id = Column(ForeignKey('course.id', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False, index=True)
    course_submission_group_id = Column(ForeignKey('course_submission_group.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    course_member_id = Column(ForeignKey('course_member.id', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False)
    course_content_id = Column(ForeignKey('course_content.id', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False)

    # Relationships
    course_content = relationship('CourseContent', back_populates='course_submission_group_members')
    course = relationship('Course')
    course_member = relationship('CourseMember', back_populates='submission_group_members')
    group = relationship("CourseSubmissionGroup", back_populates="members", uselist=False)
    created_by_user = relationship('User', foreign_keys=[created_by])
    updated_by_user = relationship('User', foreign_keys=[updated_by])


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