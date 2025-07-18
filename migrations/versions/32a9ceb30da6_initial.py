"""initial

Revision ID: 32a9ceb30da6
Revises: 
Create Date: 2025-07-07 16:20:58.568787

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '32a9ceb30da6'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('announcement',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('publication_date', sa.String(length=100), nullable=True),
    sa.Column('title', sa.String(length=500), nullable=False),
    sa.Column('price', sa.Float(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('url', sa.Text(), nullable=True),
    sa.Column('img_url', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=15), nullable=True),
    sa.Column('created_at', sa.Date(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id'),
    sa.UniqueConstraint('url')
    )
    op.create_table('bot_user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('telegram_id', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id'),
    sa.UniqueConstraint('telegram_id')
    )
    op.create_table('parser_task',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('search_query', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('periodicity', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('created_at', sa.Date(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id'),
    sa.UniqueConstraint('search_query')
    )
    op.create_table('announcement_to_task',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('announcement_id', sa.Integer(), nullable=False),
    sa.Column('task_id', sa.Integer(), nullable=False),
    sa.Column('uniq_val', sa.String(length=50), nullable=False),
    sa.Column('created_at', sa.Date(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['announcement_id'], ['announcement.id'], ),
    sa.ForeignKeyConstraint(['task_id'], ['parser_task.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id'),
    sa.UniqueConstraint('uniq_val')
    )
    op.create_table('user_to_task',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('task_id', sa.Integer(), nullable=False),
    sa.Column('uniq_val', sa.String(length=50), nullable=False),
    sa.Column('created_at', sa.Date(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['task_id'], ['parser_task.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['bot_user.telegram_id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id'),
    sa.UniqueConstraint('uniq_val')
    )
    op.create_table('viewed',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('announcement_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.Date(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['announcement_id'], ['announcement.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['bot_user.telegram_id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('viewed')
    op.drop_table('user_to_task')
    op.drop_table('announcement_to_task')
    op.drop_table('parser_task')
    op.drop_table('bot_user')
    op.drop_table('announcement')
    # ### end Alembic commands ###
