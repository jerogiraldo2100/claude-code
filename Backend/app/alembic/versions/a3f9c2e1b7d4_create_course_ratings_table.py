"""Create course_ratings table

Revision ID: a3f9c2e1b7d4
Revises: d18a08253457
Create Date: 2026-09-30 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3f9c2e1b7d4'
down_revision: Union[str, None] = 'd18a08253457'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'course_ratings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('rating', sa.SmallInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='ck_course_ratings_rating_range'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_course_ratings_id'), 'course_ratings', ['id'], unique=False)
    op.create_index(op.f('ix_course_ratings_course_id'), 'course_ratings', ['course_id'], unique=False)
    op.create_index(op.f('ix_course_ratings_user_id'), 'course_ratings', ['user_id'], unique=False)
    # One active rating per user and course (soft-deleted rows are excluded)
    op.create_index(
        'uq_course_ratings_course_user_active',
        'course_ratings',
        ['course_id', 'user_id'],
        unique=True,
        postgresql_where=sa.text('deleted_at IS NULL')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('uq_course_ratings_course_user_active', table_name='course_ratings')
    op.drop_index(op.f('ix_course_ratings_user_id'), table_name='course_ratings')
    op.drop_index(op.f('ix_course_ratings_course_id'), table_name='course_ratings')
    op.drop_index(op.f('ix_course_ratings_id'), table_name='course_ratings')
    op.drop_table('course_ratings')
