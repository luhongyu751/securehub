"""initial migration

Revision ID: 0001_initial
Revises: 
Create Date: 2026-01-11 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('username', sa.String(128), nullable=False, unique=True, index=True),
        sa.Column('hashed_password', sa.String(256), nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=True, server_default=sa.sql.expression.true()),
        sa.Column('is_admin', sa.Boolean, nullable=True, server_default=sa.sql.expression.false()),
        sa.Column('two_factor_enabled', sa.Boolean, nullable=True, server_default=sa.sql.expression.false()),
        sa.Column('otp_secret', sa.String(64), nullable=True),
    )

    op.create_table(
        'groups',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(128), nullable=False, unique=True),
        sa.Column('description', sa.String(256), nullable=True),
    )

    op.create_table(
        'user_groups',
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), primary_key=True),
        sa.Column('group_id', sa.Integer, sa.ForeignKey('groups.id'), primary_key=True),
    )

    op.create_table(
        'documents',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('filename', sa.String(512), nullable=False),
        sa.Column('file_path', sa.String(1024), nullable=False),
        sa.Column('watermark_enabled', sa.Boolean, nullable=True, server_default=sa.sql.expression.true()),
        sa.Column('watermark_text', sa.Text, nullable=True),
        sa.Column('font_size', sa.Integer, nullable=True, server_default='40'),
        sa.Column('opacity', sa.String(8), nullable=True, server_default='0.3'),
    )

    op.create_table(
        'document_access',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('document_id', sa.Integer, sa.ForeignKey('documents.id'), nullable=False),
    )

    op.create_table(
        'download_logs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id')),
        sa.Column('document_id', sa.Integer, sa.ForeignKey('documents.id')),
        sa.Column('timestamp', sa.DateTime, nullable=True),
        sa.Column('client_ip', sa.String(64), nullable=True),
    )

    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('jti', sa.String(64), nullable=False, unique=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('issued_at', sa.DateTime, nullable=True),
        sa.Column('expires_at', sa.DateTime, nullable=True),
        sa.Column('revoked', sa.Boolean, nullable=True, server_default=sa.sql.expression.false()),
    )


def downgrade():
    op.drop_table('refresh_tokens')
    op.drop_table('download_logs')
    op.drop_table('document_access')
    op.drop_table('documents')
    op.drop_table('user_groups')
    op.drop_table('groups')
    op.drop_table('users')
