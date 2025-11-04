"""Initial migration - create trees table

Revision ID: 001
Revises: 
Create Date: 2025-11-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'trees',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('source_file', sa.String(), nullable=False),
        sa.Column('bbox_xmin', sa.Integer(), nullable=False),
        sa.Column('bbox_ymin', sa.Integer(), nullable=False),
        sa.Column('bbox_xmax', sa.Integer(), nullable=False),
        sa.Column('bbox_ymax', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trees_id'), 'trees', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_trees_id'), table_name='trees')
    op.drop_table('trees')
