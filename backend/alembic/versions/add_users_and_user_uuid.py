"""add users table and user_uuid columns

Revision ID: a1b2c3d4e5f6
Revises: ef563333639d
Create Date: 2025-12-28 08:35:29.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'ef563333639d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    
    # Add user_uuid columns to all tables
    op.add_column('auth_tokens', sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('calendars', sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('day_templates', sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('days', sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('events', sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('messages', sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('push_subscriptions', sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('routines', sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('task_definitions', sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('tasks', sa.Column('user_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Create indexes on user_uuid columns
    op.create_index('idx_auth_tokens_user_uuid', 'auth_tokens', ['user_uuid'], unique=False)
    op.create_index('idx_calendars_user_uuid', 'calendars', ['user_uuid'], unique=False)
    op.create_index('idx_day_templates_user_uuid', 'day_templates', ['user_uuid'], unique=False)
    op.create_index('idx_days_user_uuid', 'days', ['user_uuid'], unique=False)
    op.create_index('idx_events_user_uuid', 'events', ['user_uuid'], unique=False)
    op.create_index('idx_messages_user_uuid', 'messages', ['user_uuid'], unique=False)
    op.create_index('idx_push_subscriptions_user_uuid', 'push_subscriptions', ['user_uuid'], unique=False)
    op.create_index('idx_routines_user_uuid', 'routines', ['user_uuid'], unique=False)
    op.create_index('idx_task_definitions_user_uuid', 'task_definitions', ['user_uuid'], unique=False)
    op.create_index('idx_tasks_user_uuid', 'tasks', ['user_uuid'], unique=False)
    
    # Add foreign key constraints
    op.create_foreign_key('fk_auth_tokens_user_uuid', 'auth_tokens', 'users', ['user_uuid'], ['id'])
    op.create_foreign_key('fk_calendars_user_uuid', 'calendars', 'users', ['user_uuid'], ['id'])
    op.create_foreign_key('fk_day_templates_user_uuid', 'day_templates', 'users', ['user_uuid'], ['id'])
    op.create_foreign_key('fk_days_user_uuid', 'days', 'users', ['user_uuid'], ['id'])
    op.create_foreign_key('fk_events_user_uuid', 'events', 'users', ['user_uuid'], ['id'])
    op.create_foreign_key('fk_messages_user_uuid', 'messages', 'users', ['user_uuid'], ['id'])
    op.create_foreign_key('fk_push_subscriptions_user_uuid', 'push_subscriptions', 'users', ['user_uuid'], ['id'])
    op.create_foreign_key('fk_routines_user_uuid', 'routines', 'users', ['user_uuid'], ['id'])
    op.create_foreign_key('fk_task_definitions_user_uuid', 'task_definitions', 'users', ['user_uuid'], ['id'])
    op.create_foreign_key('fk_tasks_user_uuid', 'tasks', 'users', ['user_uuid'], ['id'])
    
    # Note: user_uuid columns are nullable=True initially to allow existing data migration
    # After data migration, these should be set to nullable=False


def downgrade() -> None:
    """Downgrade schema."""
    # Drop foreign key constraints
    op.drop_constraint('fk_tasks_user_uuid', 'tasks', type_='foreignkey')
    op.drop_constraint('fk_task_definitions_user_uuid', 'task_definitions', type_='foreignkey')
    op.drop_constraint('fk_routines_user_uuid', 'routines', type_='foreignkey')
    op.drop_constraint('fk_push_subscriptions_user_uuid', 'push_subscriptions', type_='foreignkey')
    op.drop_constraint('fk_messages_user_uuid', 'messages', type_='foreignkey')
    op.drop_constraint('fk_events_user_uuid', 'events', type_='foreignkey')
    op.drop_constraint('fk_days_user_uuid', 'days', type_='foreignkey')
    op.drop_constraint('fk_day_templates_user_uuid', 'day_templates', type_='foreignkey')
    op.drop_constraint('fk_calendars_user_uuid', 'calendars', type_='foreignkey')
    op.drop_constraint('fk_auth_tokens_user_uuid', 'auth_tokens', type_='foreignkey')
    
    # Drop indexes
    op.drop_index('idx_tasks_user_uuid', table_name='tasks')
    op.drop_index('idx_task_definitions_user_uuid', table_name='task_definitions')
    op.drop_index('idx_routines_user_uuid', table_name='routines')
    op.drop_index('idx_push_subscriptions_user_uuid', table_name='push_subscriptions')
    op.drop_index('idx_messages_user_uuid', table_name='messages')
    op.drop_index('idx_events_user_uuid', table_name='events')
    op.drop_index('idx_days_user_uuid', table_name='days')
    op.drop_index('idx_day_templates_user_uuid', table_name='day_templates')
    op.drop_index('idx_calendars_user_uuid', table_name='calendars')
    op.drop_index('idx_auth_tokens_user_uuid', table_name='auth_tokens')
    
    # Drop user_uuid columns
    op.drop_column('tasks', 'user_uuid')
    op.drop_column('task_definitions', 'user_uuid')
    op.drop_column('routines', 'user_uuid')
    op.drop_column('push_subscriptions', 'user_uuid')
    op.drop_column('messages', 'user_uuid')
    op.drop_column('events', 'user_uuid')
    op.drop_column('days', 'user_uuid')
    op.drop_column('day_templates', 'user_uuid')
    op.drop_column('calendars', 'user_uuid')
    op.drop_column('auth_tokens', 'user_uuid')
    
    # Drop users table
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')

