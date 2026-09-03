"""Add total_records to chat_messages

Revision ID: 8bdf050d77e5
Revises: 7acf050d77d4
Create Date: 2026-09-03 19:12:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8bdf050d77e5'
down_revision: Union[str, Sequence[str], None] = '7acf050d77d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('chat_messages', sa.Column('total_records', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('chat_messages', 'total_records')
