from typing import Text # coding: utf-8
from sqlalchemy import BigInteger, Boolean, CheckConstraint, Column, DateTime, Enum, Float, ForeignKey, Index, Integer, String, UniqueConstraint, select, text, Table, ForeignKeyConstraint, Computed
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import relationship, column_property, Mapped
from sqlalchemy_utils import LtreeType
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class CourseContentKind(Base):
    __tablename__ = 'course_content_kind'

    id = Column(String(255), primary_key=True)
    title = Column(String(255))
    description = Column(String(4096))
    has_ascendants = Column(Boolean, nullable=False)
    has_descendants = Column(Boolean, nullable=False)
    submittable = Column(Boolean, nullable=False)


class CourseRole(Base):
    __tablename__ = 'course_role'

    id = Column(String(255), primary_key=True)
    title = Column(String(255))
    description = Column(String(4096))


class Group(Base):
    __tablename__ = 'group'
    __table_args__ = (
        CheckConstraint('ctutor_valid_slug((slug)::text)'),
    )

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(UUID)
    updated_by = Column(UUID)
    properties = Column(JSONB(astext_type=Text()))
    title = Column(String(255))
    description = Column(String(4096))
    slug = Column(String(255), nullable=False)
    type = Column(Enum('fixed', 'dynamic', name='ctutor_group_type'), server_default=text("'fixed'::ctutor_group_type"))


class Role(Base):
    __tablename__ = 'role'
    __table_args__ = (
        CheckConstraint("(NOT builtin) OR ((id)::text ~ '^_'::text)"),
        CheckConstraint('(builtin AND ctutor_valid_slug(SUBSTRING(id FROM 2))) OR ((NOT builtin) AND ctutor_valid_slug((id)::text))')
    )

    id = Column(String(255), primary_key=True)
    title = Column(String(255))
    description = Column(String(4096))
    builtin = Column(Boolean, nullable=False, server_default=text("false"))


class User(Base):
    __tablename__ = 'user'
    __table_args__ = (
        CheckConstraint(
            "(user_type <> 'token') OR (token_expiration IS NOT NULL)",
            name='ck_user_token_expiration'
        ),
    )

    number = Column(String(255), unique=True)
    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    updated_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    properties = Column(JSONB(astext_type=Text()))
    archived_at = Column(DateTime(True))
    given_name = Column(String(255))
    family_name = Column(String(255))
    email = Column(String(320), unique=True)
    user_type = Column(Enum('user', 'token', name='user_type'), nullable=False, server_default=text("'user'::user_type"))
    fs_number = Column(BigInteger, nullable=False, server_default=text("nextval('user_unique_fs_number_seq'::regclass)"))
    token_expiration = Column(DateTime(True))
    username = Column(String(255), unique=True)
    password = Column(String(255))

    course_members = relationship("CourseMember", foreign_keys="CourseMember.user_id", back_populates="user", uselist=True,  lazy="select")
    student_profiles = relationship("StudentProfile", foreign_keys="StudentProfile.user_id", back_populates="user", uselist=True, lazy="select")

class Account(Base):
    __tablename__ = 'account'
    __table_args__ = (
        Index('account_provider_type_provider_account_id_key', 'provider', 'type', 'provider_account_id', unique=True),
        Index('account_provider_type_user_id_key', 'provider', 'type', 'user_id', unique=True)
    )

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(UUID)
    updated_by = Column(UUID)
    properties = Column(JSONB(astext_type=Text()))
    provider = Column(String(255), nullable=False)
    type = Column(String(63), nullable=False)
    provider_account_id = Column(String(255), nullable=False)
    user_id = Column(ForeignKey('user.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False, index=True)

    user = relationship('User')


class ExecutionBackend(Base):
    __tablename__ = 'execution_backend'
    __table_args__ = (
        CheckConstraint("(slug)::text ~* '^[A-Za-z0-9_-]+$'::text"),
    )

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    updated_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    properties = Column(JSONB(astext_type=Text()))
    type = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True)

    user = relationship('User', primaryjoin='ExecutionBackend.created_by == User.id')
    user1 = relationship('User', primaryjoin='ExecutionBackend.updated_by == User.id')

class GroupClaim(Base):
    __tablename__ = 'group_claim'

    group_id = Column(ForeignKey('group.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    claim_type = Column(String(255), primary_key=True, nullable=False)
    claim_value = Column(String(255), primary_key=True, nullable=False)
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(UUID)
    updated_by = Column(UUID)
    properties = Column(JSONB(astext_type=Text()))

    group = relationship('Group')

class Organization(Base):
    __tablename__ = 'organization'
    __table_args__ = (
        CheckConstraint("((organization_type = 'user'::organization_type) AND (title IS NULL)) OR ((organization_type <> 'user'::organization_type) AND (title IS NOT NULL))"),
        CheckConstraint("((organization_type = 'user'::organization_type) AND (user_id IS NOT NULL)) OR ((organization_type <> 'user'::organization_type) AND (user_id IS NULL))"),
        # ForeignKeyConstraint(['organization_type', 'parent_path'], ['organization.organization_type', 'organization.path'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
        Index('organization_path_key', 'organization_type', 'path', unique=True),
        Index('organization_number_key', 'organization_type', 'number', unique=True)
    )

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    updated_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    properties = Column(JSONB(astext_type=Text()))
    number = Column(String(255))
    title = Column(String(255))
    description = Column(String(4096))
    archived_at = Column(DateTime(True))
    email = Column(String(320))
    telephone = Column(String(255))
    fax_number = Column(String(255))
    url = Column(String(2048))
    postal_code = Column(String(255))
    street_address = Column(String(1024))
    locality = Column(String(255))
    region = Column(String(255))
    country = Column(String(255))
    organization_type = Column(Enum('user', 'community', 'organization', name='organization_type'), nullable=False, index=True)
    user_id = Column(ForeignKey('user.id', ondelete='CASCADE', onupdate='RESTRICT'), unique=True)
    path = Column(LtreeType, nullable=False, index=True)
#     parent_path = Column(LtreeType, Computed('''
# CASE
#     WHEN (nlevel(path) > 1) THEN subpath(path, 0, (nlevel(path) - 1))
#     ELSE NULL::ltree
# END''', persisted=True))

    user = relationship('User', primaryjoin='Organization.created_by == User.id')
    # parent = relationship('Organization', remote_side=[id])
    user1 = relationship('User', primaryjoin='Organization.updated_by == User.id')
    user2 = relationship('User', primaryjoin='Organization.user_id == User.id')


class Profile(Base):
    __tablename__ = 'profile'

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(UUID)
    updated_by = Column(UUID)
    properties = Column(JSONB(astext_type=Text()))
    avatar_color = Column(Integer)
    avatar_image = Column(String(2048))
    nickname = Column(String(255), unique=True)
    bio = Column(String(16384))
    url = Column(String(2048))
    user_id = Column(ForeignKey('user.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False, unique=True)

    user = relationship('User')


class RoleClaim(Base):
    __tablename__ = 'role_claim'

    role_id = Column(ForeignKey('role.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    claim_type = Column(String(255), primary_key=True, nullable=False)
    claim_value = Column(String(255), primary_key=True, nullable=False)
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(UUID)
    updated_by = Column(UUID)
    properties = Column(JSONB(astext_type=Text()))

    role = relationship('Role')


class Session(Base):
    __tablename__ = 'session'

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(UUID)
    updated_by = Column(UUID)
    properties = Column(JSONB(astext_type=Text()))
    user_id = Column(ForeignKey('user.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    session_id = Column(String(1024), nullable=False)
    logout_time = Column(DateTime(True))
    ip_address = Column(INET, nullable=False)

    user = relationship('User')


class StudentProfile(Base):
    __tablename__ = 'student_profile'

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(UUID)
    updated_by = Column(UUID)
    properties = Column(JSONB(astext_type=Text()))
    student_id = Column(String(255), unique=True)
    student_email = Column(String(320), unique=True)
    user_id = Column(ForeignKey('user.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False, unique=True)

    user = relationship('User', foreign_keys=[user_id], back_populates="student_profiles", uselist=False)

class UserGroup(Base):
    __tablename__ = 'user_group'

    user_id = Column(ForeignKey('user.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    group_id = Column(ForeignKey('group.id', ondelete='RESTRICT', onupdate='CASCADE'), primary_key=True, nullable=False)
    transient = Column(Boolean, server_default=text("false"))
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(UUID)
    updated_by = Column(UUID)

    group = relationship('Group')
    user = relationship('User')


class UserRole(Base):
    __tablename__ = 'user_role'

    user_id = Column(ForeignKey('user.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    role_id = Column(ForeignKey('role.id', ondelete='RESTRICT', onupdate='CASCADE'), primary_key=True, nullable=False)
    transient = Column(Boolean, server_default=text("false"))
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(UUID)
    updated_by = Column(UUID)

    role = relationship('Role')
    user = relationship('User')


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
    properties = Column(JSONB(astext_type=Text()))
    title = Column(String(255))
    description = Column(String(4096))
    path = Column(LtreeType, nullable=False)
    organization_id = Column(ForeignKey('organization.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)

    user = relationship('User', primaryjoin='CourseFamily.created_by == User.id')
    organization = relationship('Organization')
    user1 = relationship('User', primaryjoin='CourseFamily.updated_by == User.id')


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
    properties = Column(JSONB(astext_type=Text()))
    title = Column(String(255))
    description = Column(String(4096))
    path = Column(LtreeType, nullable=False)
    course_family_id = Column(ForeignKey('course_family.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    organization_id = Column(ForeignKey('organization.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    version_identifier = Column(String(2048))

    course_family = relationship('CourseFamily')
    user = relationship('User', primaryjoin='Course.created_by == User.id')
    organization = relationship('Organization')
    user1 = relationship('User', primaryjoin='Course.updated_by == User.id')

    course_members = relationship("CourseMember", foreign_keys="CourseMember.course_id", back_populates="course", uselist=True, lazy="select")
    course_content_types = relationship("CourseContentType", foreign_keys="CourseContentType.course_id", back_populates="course", uselist=True, lazy="select")

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
    properties = Column(JSONB(astext_type=Text()))
    title = Column(String(255))
    description = Column(String(4096))
    slug = Column(String(255), nullable=False)
    color = Column(Enum('red', 'orange', 'amber', 'yellow', 'lime', 'green', 'emerald', 'teal', 'cyan', 'sky', 'blue', 'indigo', 'violet', 'purple', 'fuchsia', 'pink', 'rose', name='ctutor_color'))
    course_content_kind_id = Column(ForeignKey('course_content_kind.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    course_id = Column(ForeignKey('course.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)

    course_contents = relationship("CourseContent", foreign_keys="CourseContent.course_content_type_id", back_populates="course_content_type", uselist=True, lazy="select")
    course_content_kind = relationship('CourseContentKind')
    course = relationship("Course", foreign_keys=[course_id], back_populates="course_content_types", lazy="select")
    user = relationship('User', primaryjoin='CourseContentType.created_by == User.id')
    user1 = relationship('User', primaryjoin='CourseContentType.updated_by == User.id')


class CourseExecutionBackend(Base):
    __tablename__ = 'course_execution_backend'

    execution_backend_id = Column(ForeignKey('execution_backend.id', ondelete='CASCADE', onupdate='RESTRICT'), primary_key=True, nullable=False)
    course_id = Column(ForeignKey('course.id', ondelete='CASCADE', onupdate='RESTRICT'), primary_key=True, nullable=False)
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(UUID)
    updated_by = Column(UUID)
    properties = Column(JSONB(astext_type=Text()))

    course = relationship('Course')
    execution_backend = relationship('ExecutionBackend')


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
    properties = Column(JSONB(astext_type=Text()))
    title = Column(String(255))
    description = Column(String(4096))
    course_id = Column(ForeignKey('course.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)

    course = relationship('Course')
    user = relationship('User', primaryjoin='CourseGroup.created_by == User.id')
    user1 = relationship('User', primaryjoin='CourseGroup.updated_by == User.id')


class CourseContent(Base):
    __tablename__ = 'course_content'
    __table_args__ = (
        ForeignKeyConstraint(['course_id', 'course_content_type_id'], ['course_content_type.course_id', 'course_content_type.id'], ondelete='RESTRICT', onupdate='RESTRICT'),
        Index('course_content_path_key', 'course_id', 'path', unique=True)
    )

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    updated_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    properties = Column(JSONB(astext_type=Text()))
    archived_at = Column(DateTime(True))
    title = Column(String(255))
    description = Column(String(4096))
    path = Column(LtreeType, nullable=False)
    course_id = Column(ForeignKey('course.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    course_content_type_id = Column(ForeignKey('course_content_type.id', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False)
    version_identifier = Column(String(2048), nullable=False)
    position = Column(Float(53), nullable=False)
    max_group_size = Column(Integer, nullable=False)
    max_test_runs = Column(Integer)
    max_submissions = Column(Integer)
    execution_backend_id = Column(ForeignKey('execution_backend.id', ondelete='CASCADE', onupdate='RESTRICT'))

    #course_content_type = relationship('CourseContentType', foreign_keys=course_content_type_id)
    course_content_type = relationship('CourseContentType', primaryjoin='CourseContent.course_content_type_id == CourseContentType.id')
    course = relationship('CourseContentType', primaryjoin='CourseContent.course_id == CourseContentType.course_id')
    #course1 = relationship('Course')
    user = relationship('User', primaryjoin='CourseContent.created_by == User.id')
    user1 = relationship('User', primaryjoin='CourseContent.updated_by == User.id')

    course_content_type = relationship("CourseContentType", foreign_keys=[course_content_type_id], back_populates="course_contents", lazy="select")

    course_content_kind_id = column_property(select(CourseContentKind.id).where(CourseContentKind.id == CourseContentType.course_content_kind_id, CourseContentType.id == course_content_type_id).scalar_subquery());

    results: Mapped[list["Result"]] = relationship('Result', back_populates="course_content", uselist=True, cascade='all,delete')

class CourseMember(Base):
    __tablename__ = 'course_member'
    __table_args__ = (
        CheckConstraint("""
CASE
    WHEN ((course_role_id)::text = '_student'::text) THEN (course_group_id IS NOT NULL)
    ELSE true
END"""),
        ForeignKeyConstraint(['course_id', 'course_group_id'], ['course_group.course_id', 'course_group.id'], ondelete='RESTRICT', onupdate='RESTRICT'),
        Index('course_member_key', 'user_id', 'course_id', unique=True)
    )

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    updated_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    properties = Column(JSONB(astext_type=Text()))
    user_id = Column(ForeignKey('user.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    course_id = Column(ForeignKey('course.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    course_group_id = Column(ForeignKey('course_group.id', ondelete='RESTRICT', onupdate='RESTRICT'))
    course_role_id = Column(ForeignKey('course_role.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)

    course_group = relationship('CourseGroup', primaryjoin='CourseMember.course_group_id == CourseGroup.id')
    # course = relationship('CourseGroup', primaryjoin='CourseMember.course_id == CourseGroup.course_id')
    course = relationship("Course", foreign_keys=[course_id], back_populates="course_members",  lazy="select")
    # course1 = relationship('Course')
    course_role = relationship('CourseRole')
    #user = relationship('User', primaryjoin='CourseMember.user_id == User.id')
    created_by_user = relationship('User', foreign_keys=[created_by])
    updated_by_user = relationship('User', foreign_keys=[updated_by])
    #submission_groups = relationship('CourseSubmissionGroup', secondary='course_submission_group_member')

    comments_written = relationship("CourseMemberComment", foreign_keys="CourseMemberComment.transmitter_id", back_populates="transmitter", uselist=True, lazy="select")

    user = relationship("User", foreign_keys=[user_id], back_populates="course_members", uselist=False, lazy="select")


class CourseSubmissionGroup(Base):
    __tablename__ = 'course_submission_group'

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    updated_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    properties = Column(JSONB(astext_type=Text()))
    status = Column(String(2048))
    grading = Column(Float(53))
    max_group_size = Column(Integer, nullable=False)
    max_test_runs = Column(Integer)
    max_submissions = Column(Integer)
    course_id = Column(ForeignKey('course.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    course_content_id = Column(ForeignKey('course_content.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)

    course_content = relationship('CourseContent')
    course = relationship('Course')
    # user = relationship('User', primaryjoin='CourseSubmissionGroup.created_by == User.id')
    # user1 = relationship('User', primaryjoin='CourseSubmissionGroup.updated_by == User.id')

    members = relationship("CourseSubmissionGroupMember", back_populates="group", uselist=True)


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
    properties = Column(JSONB(astext_type=Text()))
    grading = Column(Float(53))
    course_id = Column(ForeignKey('course.id', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False, index=True)
    course_submission_group_id = Column(ForeignKey('course_submission_group.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    course_member_id = Column(ForeignKey('course_member.id', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False)
    course_content_id = Column(ForeignKey('course_content.id', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False)

    course_content = relationship('CourseContent')
    # course_member = relationship('CourseMember', primaryjoin='CourseSubmissionGroupMember.course_member_id == CourseMember.id') # TODO: fix backpopulate
    # course_submission_group = relationship('CourseSubmissionGroup') # TODO: fix backpopulate
    # user = relationship('User', primaryjoin='CourseSubmissionGroupMember.created_by == User.id')
    # user1 = relationship('User', primaryjoin='CourseSubmissionGroupMember.updated_by == User.id')
    
    group = relationship("CourseSubmissionGroup", foreign_keys=[course_submission_group_id], back_populates="members", uselist=False)


class Result(Base):
    __tablename__ = 'result'
    __table_args__ = (
        Index('result_commit_test_system_key', 'test_system_id', 'execution_backend_id', unique=True),
        Index('result_version_identifier_member_key', 'course_member_id', 'version_identifier', unique=True),
        Index('result_version_identifier_group_key', 'course_submission_group_id', 'version_identifier', unique=True)
    )

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    updated_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    properties = Column(JSONB(astext_type=Text()))
    submit = Column(Boolean, nullable=False)
    course_member_id = Column(ForeignKey('course_member.id', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False, index=True)
    course_submission_group_id = Column(ForeignKey('course_submission_group.id', ondelete='SET NULL', onupdate='RESTRICT'), index=True)
    course_content_id = Column(ForeignKey('course_content.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False, index=True)
    course_content_type_id = Column(ForeignKey('course_content_type.id', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False)
    execution_backend_id = Column(ForeignKey('execution_backend.id', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False)
    test_system_id = Column(String(255), nullable=False)
    result = Column(Float(53), nullable=False)
    result_json = Column(JSONB(astext_type=Text()))
    version_identifier = Column(String(2048), nullable=False)
    status = Column(Integer, nullable=False)

    course_content: Mapped["CourseContent"] = relationship('CourseContent', back_populates="results", uselist=False, cascade='all,delete')
    course_content_type = relationship('CourseContentType')
    course_member = relationship('CourseMember')
    course_submission_group = relationship('CourseSubmissionGroup')
    user = relationship('User', primaryjoin='Result.created_by == User.id')
    execution_backend = relationship('ExecutionBackend')
    user1 = relationship('User', primaryjoin='Result.updated_by == User.id')

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

    transmitter = relationship("CourseMember", foreign_keys=[transmitter_id], back_populates="comments_written", lazy="select")