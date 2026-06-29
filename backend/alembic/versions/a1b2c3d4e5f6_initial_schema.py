"""Initial schema — v3 (all tables)

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-06-27
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table('users',
        sa.Column('id',             sa.String(36),           nullable=False),
        sa.Column('first_name',     sa.String(100),          nullable=False),
        sa.Column('last_name',      sa.String(100),          nullable=False),
        sa.Column('middle_name',    sa.String(100),          nullable=True),
        sa.Column('email',          sa.String(255),          nullable=False),
        sa.Column('recovery_email', sa.String(255),          nullable=True),
        sa.Column('password_hash',  sa.String(255),          nullable=False),
        sa.Column('avatar_url',     sa.String(512),          nullable=True),
        sa.Column('is_active',      sa.Boolean(),            nullable=False, server_default='1'),
        sa.Column('last_login_at',  sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at',     sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at',     sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at',     sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # ── roles ──────────────────────────────────────────────────────────────────
    op.create_table('roles',
        sa.Column('id',          sa.String(36),  nullable=False),
        sa.Column('name',        sa.String(100), nullable=False),
        sa.Column('description', sa.Text(),      nullable=True),
        sa.Column('is_system',   sa.Boolean(),   nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    # ── permissions ────────────────────────────────────────────────────────────
    op.create_table('permissions',
        sa.Column('id',          sa.String(36),  nullable=False),
        sa.Column('code',        sa.String(100), nullable=False),
        sa.Column('resource',    sa.String(100), nullable=False),
        sa.Column('action',      sa.String(50),  nullable=False),
        sa.Column('description', sa.Text(),      nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )
    op.create_index('ix_permissions_code', 'permissions', ['code'], unique=True)

    # ── access_tokens ──────────────────────────────────────────────────────────
    op.create_table('access_tokens',
        sa.Column('id',         sa.String(36),  nullable=False),
        sa.Column('user_id',    sa.String(36),  nullable=False),
        sa.Column('token',      sa.String(64),  nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('user_agent', sa.String(512), nullable=True),
        sa.Column('ip_address', sa.String(45),  nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token'),
    )
    op.create_index('ix_access_tokens_token',   'access_tokens', ['token'],   unique=True)
    op.create_index('ix_access_tokens_user_id', 'access_tokens', ['user_id'])

    # ── user_roles ─────────────────────────────────────────────────────────────
    op.create_table('user_roles',
        sa.Column('id',      sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('role_id', sa.String(36), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'role_id', name='uq_user_role'),
    )

    # ── role_permissions ───────────────────────────────────────────────────────
    op.create_table('role_permissions',
        sa.Column('id',            sa.String(36), nullable=False),
        sa.Column('role_id',       sa.String(36), nullable=False),
        sa.Column('permission_id', sa.String(36), nullable=False),
        sa.ForeignKeyConstraint(['role_id'],       ['roles.id'],       ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role_id', 'permission_id', name='uq_role_permission'),
    )

    # ── password_resets ────────────────────────────────────────────────────────
    op.create_table('password_resets',
        sa.Column('id',         sa.String(36), nullable=False),
        sa.Column('user_id',    sa.String(36), nullable=False),
        sa.Column('token',      sa.String(64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used',       sa.Boolean(),  nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token'),
    )

    # ── audit_log ──────────────────────────────────────────────────────────────
    op.create_table('audit_log',
        sa.Column('id',          sa.String(36),  nullable=False),
        sa.Column('user_id',     sa.String(36),  nullable=True),
        sa.Column('action',      sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(100), nullable=True),
        sa.Column('entity_id',   sa.String(36),  nullable=True),
        sa.Column('detail',      sa.Text(),      nullable=True),
        sa.Column('ip_address',  sa.String(45),  nullable=True),
        sa.Column('created_at',  sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_log_user_id',    'audit_log', ['user_id'])
    op.create_index('ix_audit_log_created_at', 'audit_log', ['created_at'])

    # ── notifications ──────────────────────────────────────────────────────────
    op.create_table('notifications',
        sa.Column('id',         sa.String(36),  nullable=False),
        sa.Column('user_id',    sa.String(36),  nullable=True),
        sa.Column('event',      sa.String(100), nullable=False),
        sa.Column('title',      sa.String(255), nullable=False),
        sa.Column('body',       sa.Text(),      nullable=True),
        sa.Column('link',       sa.String(512), nullable=True),
        sa.Column('is_read',    sa.Boolean(),   nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── user_totp (2FA) ────────────────────────────────────────────────────────
    op.create_table('user_totp',
        sa.Column('id',         sa.String(36), nullable=False),
        sa.Column('user_id',    sa.String(36), nullable=False),
        sa.Column('secret',     sa.String(64), nullable=False),
        sa.Column('is_enabled', sa.Boolean(),  nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index('ix_user_totp_user_id', 'user_totp', ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_user_totp_user_id',    table_name='user_totp')
    op.drop_table('user_totp')
    op.drop_table('notifications')
    op.drop_index('ix_audit_log_created_at', table_name='audit_log')
    op.drop_index('ix_audit_log_user_id',    table_name='audit_log')
    op.drop_table('audit_log')
    op.drop_table('password_resets')
    op.drop_table('role_permissions')
    op.drop_table('user_roles')
    op.drop_index('ix_access_tokens_user_id', table_name='access_tokens')
    op.drop_index('ix_access_tokens_token',   table_name='access_tokens')
    op.drop_table('access_tokens')
    op.drop_index('ix_permissions_code', table_name='permissions')
    op.drop_table('permissions')
    op.drop_table('roles')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
