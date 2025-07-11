from typing import Text
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Float, 
    ForeignKey, Index, Integer, String, text
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship, Mapped

from .base import Base


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

    # Relationships
    course_content: Mapped["CourseContent"] = relationship('CourseContent', back_populates="results", uselist=False, cascade='all,delete')
    course_content_type = relationship('CourseContentType', back_populates='results')
    course_member = relationship('CourseMember', back_populates='results')
    course_submission_group = relationship('CourseSubmissionGroup', back_populates='results')
    created_by_user = relationship('User', foreign_keys=[created_by])
    updated_by_user = relationship('User', foreign_keys=[updated_by])
    execution_backend = relationship('ExecutionBackend', back_populates='results')