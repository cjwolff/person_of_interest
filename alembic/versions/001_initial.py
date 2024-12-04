"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-03-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create photo_notes table
    op.create_table(
        'photo_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('photo_url', sa.String(), nullable=False),
        sa.Column('note', sa.String(), nullable=True),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('faces', postgresql.JSONB(), nullable=True),
        sa.Column('objects', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_photo_notes_user_id', 'photo_notes', ['user_id'])
    op.create_index('idx_photo_notes_location', 'photo_notes', ['latitude', 'longitude'])

    # Create behavior_analyses table
    op.create_table(
        'behavior_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('photo_note_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('risk_level', sa.Enum('LOW', 'MEDIUM', 'HIGH', name='risk_level'), nullable=False),
        sa.Column('behaviors', postgresql.JSONB(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('pose_data', postgresql.JSONB(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['photo_note_id'], ['photo_notes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_behavior_analyses_photo_note_id', 'behavior_analyses', ['photo_note_id'])
    op.create_index('idx_behavior_analyses_timestamp', 'behavior_analyses', ['timestamp'])

    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=False),
        sa.Column('distance', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.Enum('LOW', 'MEDIUM', 'HIGH', name='risk_level'), nullable=False),
        sa.Column('is_dismissed', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['target_id'], ['photo_notes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_alerts_user_id', 'alerts', ['user_id'])
    op.create_index('idx_alerts_target_id', 'alerts', ['target_id'])
    op.create_index('idx_alerts_created_at', 'alerts', ['created_at'])

def downgrade():
    op.drop_table('alerts')
    op.drop_table('behavior_analyses')
    op.drop_table('photo_notes')
    op.execute('DROP TYPE risk_level')