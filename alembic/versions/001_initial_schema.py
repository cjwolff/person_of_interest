"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-02-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship, ForeignKey

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create detections table
    op.create_table(
        'detections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('frame_id', sa.String(), nullable=False),
        sa.Column('object_type', sa.String(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('bbox', JSON, nullable=False),
        sa.Column('detection_metadata', JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create behavior_patterns table
    op.create_table(
        'behavior_patterns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('movement_pattern', JSON, nullable=False),
        sa.Column('interaction_pattern', JSON, nullable=False),
        sa.Column('anomalies', JSON, nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create geofence_events table
    op.create_table(
        'geofence_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('geofence_id', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('location', JSON, nullable=False),
        sa.Column('event_metadata', JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create geofence_zones table
    op.create_table(
        'geofence_zones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('zone_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('boundaries', JSON, nullable=False),
        sa.Column('zone_type', sa.String(), nullable=False),
        sa.Column('risk_level', sa.Float(), nullable=False),
        sa.Column('zone_metadata', JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create face_detections table
    op.create_table(
        'face_detections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('detection_id', sa.Integer(), ForeignKey("detections.id")),
        sa.Column('face_encoding', JSON, nullable=False),
        sa.Column('landmarks', JSON, nullable=True),
        sa.Column('face_metadata', JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('geofence_zones')
    op.drop_table('geofence_events')
    op.drop_table('behavior_patterns')
    op.drop_table('detections')
    op.drop_table('face_detections') 