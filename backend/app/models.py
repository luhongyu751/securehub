from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(128), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    two_factor_enabled = Column(Boolean, default=False)
    otp_secret = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # relationship shortcuts
    groups = relationship('Group', secondary='user_groups', back_populates='users')



from sqlalchemy import Table

# association table for user groups
user_groups = Table(
    'user_groups', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True),
)


class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(512), nullable=False)
    file_path = Column(String(1024), nullable=False)
    watermark_enabled = Column(Boolean, default=True)
    watermark_text = Column(Text, nullable=True)
    font_size = Column(Integer, default=40)
    opacity = Column(String(8), default='0.3')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    accesses = relationship('DocumentAccess', back_populates='document', cascade='all, delete-orphan')


class DocumentAccess(Base):
    __tablename__ = 'document_access'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    __table_args__ = (UniqueConstraint('user_id', 'document_id', name='uix_user_document'),)
    user = relationship('User', backref='document_accesses')
    document = relationship('Document', back_populates='accesses')


class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True)
    name = Column(String(128), unique=True, nullable=False)
    description = Column(String(256), nullable=True)
    users = relationship('User', secondary=user_groups, back_populates='groups')


class DownloadLog(Base):
    __tablename__ = 'download_logs'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    document_id = Column(Integer, ForeignKey('documents.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    client_ip = Column(String(64), nullable=True)
    user = relationship('User', backref='download_logs')
    document = relationship('Document', backref='download_logs')


class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True)
    actor_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    action = Column(String(128), nullable=False)
    object_type = Column(String(64), nullable=True)
    object_id = Column(String(64), nullable=True)
    detail = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    actor = relationship('User', backref='audit_logs')


class RefreshToken(Base):
    __tablename__ = 'refresh_tokens'
    id = Column(Integer, primary_key=True)
    jti = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    issued_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    revoked = Column(Boolean, default=False)
