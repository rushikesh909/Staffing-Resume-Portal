"""initial schema

Revision ID: 0001
Revises: 
Create Date: 2026-11-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'clients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('contact_email', sa.String(length=200), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('contact_email'),
    )

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=200), nullable=False),
        sa.Column('hashed_password', sa.String(length=200), nullable=False),
        sa.Column('role', sa.Enum('recruiter', 'client_hiring_manager', name='userrole'), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.create_table(
        'requisitions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('jd_text', sa.Text(), nullable=False),
        sa.Column('scorecard', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='active', nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'candidates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('email', sa.String(length=200), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('current_role', sa.String(length=200), nullable=True),
        sa.Column('experience_years', sa.Float(), nullable=True),
        sa.Column('notice_days', sa.Integer(), nullable=True),
        sa.Column('skills', sa.JSON(), nullable=True),
        sa.Column('cv_path', sa.String(length=500), nullable=True),
        sa.Column('cv_text', sa.Text(), nullable=True),
        sa.Column('parsed_data', sa.JSON(), nullable=True),
        sa.Column('fingerprint', sa.String(length=200), nullable=True),
        sa.Column('consent_given', sa.Boolean(), server_default=sa.text('false'), nullable=True),
        sa.Column('consent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_candidates_fingerprint'), 'candidates', ['fingerprint'], unique=False)

    op.create_table(
        'requisition_candidates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('requisition_id', sa.Integer(), nullable=False),
        sa.Column('candidate_id', sa.Integer(), nullable=False),
        sa.Column('ai_score', sa.Float(), nullable=True),
        sa.Column('score_evidence', sa.JSON(), nullable=True),
        sa.Column('pipeline_stage', sa.Enum('sourced', 'screened', 'submitted_to_client', 'client_reviewed', 'interview_scheduled', 'offer_made', 'joined', name='pipelinestage'), server_default='sourced', nullable=True),
        sa.Column('submitted_to_client', sa.Boolean(), server_default=sa.text('false'), nullable=True),
        sa.Column('viewed_by_recruiter', sa.Boolean(), server_default=sa.text('false'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id']),
        sa.ForeignKeyConstraint(['requisition_id'], ['requisitions.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'client_submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('requisition_candidate_id', sa.Integer(), nullable=False),
        sa.Column('client_decision', sa.Enum('shortlisted', 'rejected', 'interview_proposed', name='clientdecision'), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('proposed_slot', sa.String(length=200), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['requisition_candidate_id'], ['requisition_candidates.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('candidate_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('audit_log')
    op.drop_table('client_submissions')
    op.drop_table('requisition_candidates')
    op.drop_table('candidates')
    op.drop_table('requisitions')
    op.drop_table('users')
    op.drop_table('clients')
