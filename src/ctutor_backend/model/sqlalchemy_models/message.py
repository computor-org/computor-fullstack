from typing import Text
from sqlalchemy import (
    BigInteger, Column, DateTime, ForeignKey, 
    Index, String, text, Integer
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .base import Base


class Message(Base):
    __tablename__ = 'codeability_message'
    __table_args__ = (
        Index('codeability_message_course_id_archived_at_key', 'course_id', 'archived_at'),
        Index('codeability_message_parent_id_archived_at_key', 'parent_id', 'archived_at'),
        Index('codeability_message_transmitter_course_member_id_archived_at_key', 'transmitter_course_member_id', 'archived_at'),
    )

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    updated_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    properties = Column(JSONB(astext_type=Text()))
    archived_at = Column(DateTime(True))
    course_id = Column(ForeignKey('course.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    transmitter_course_member_id = Column(ForeignKey('course_member.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    parent_id = Column(ForeignKey('codeability_message.id', ondelete='CASCADE', onupdate='RESTRICT'))
    level = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(String(16384), nullable=False)

    # Relationships
    course = relationship('Course')
    transmitter = relationship('CourseMember', foreign_keys=[transmitter_course_member_id])
    parent = relationship('Message', remote_side=[id], backref='replies')
    created_by_user = relationship('User', foreign_keys=[created_by])
    updated_by_user = relationship('User', foreign_keys=[updated_by])
    message_reads = relationship('MessageRead', back_populates='message', cascade='all, delete-orphan')


class MessageRead(Base):
    __tablename__ = 'codeability_message_read'
    __table_args__ = (
        Index('codeability_message_read_key', 'codeability_message_id', 'course_member_id', unique=True),
    )

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    version = Column(BigInteger, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    created_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    updated_by = Column(ForeignKey('user.id', ondelete='SET NULL'))
    properties = Column(JSONB(astext_type=Text()))
    codeability_message_id = Column(ForeignKey('codeability_message.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)
    course_member_id = Column(ForeignKey('course_member.id', ondelete='CASCADE', onupdate='RESTRICT'), nullable=False)

    # Relationships
    message = relationship('Message', back_populates='message_reads')
    course_member = relationship('CourseMember')
    created_by_user = relationship('User', foreign_keys=[created_by])
    updated_by_user = relationship('User', foreign_keys=[updated_by])