"""add roles for members

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-02 22:32:17.518716
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, Sequence[str], None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # створюємо ENUM тип у PostgreSQL
    company_role_enum = postgresql.ENUM('member', 'admin', name='companyrole', create_type=True)
    company_role_enum.create(op.get_bind())

    # додаємо колонку role до таблиці company_members
    with op.batch_alter_table('company_members', schema=None) as batch_op:
        batch_op.add_column(sa.Column('role', sa.Enum('member', 'admin', name='companyrole'), nullable=False, server_default='member'))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False))


def downgrade() -> None:
    # видаляємо колонки
    with op.batch_alter_table('company_members', schema=None) as batch_op:
        batch_op.drop_column('updated_at')
        batch_op.drop_column('role')

    # видаляємо ENUM тип
    company_role_enum = postgresql.ENUM('member', 'admin', name='companyrole')
    company_role_enum.drop(op.get_bind())
