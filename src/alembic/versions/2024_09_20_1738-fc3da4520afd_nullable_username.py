"""nullable username

Revision ID: fc3da4520afd
Revises: 84c923437bd1
Create Date: 2024-09-20 17:38:22.169073

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'fc3da4520afd'
down_revision: Union[str, None] = '84c923437bd1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('solutions') as batch_op:
        batch_op.alter_column('author_id',
                              existing_type=sa.BIGINT(),
                              nullable=True,
                              existing_server_default=sa.text("'1'"))
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('username',
                              existing_type=sa.VARCHAR(),
                              nullable=True,
                              existing_server_default=sa.text("'-'"))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'username',
                    existing_type=sa.VARCHAR(),
                    nullable=False,
                    existing_server_default=sa.text("'-'"))
    op.alter_column('solutions', 'author_id',
                    existing_type=sa.BIGINT(),
                    nullable=False,
                    existing_server_default=sa.text("'1'"))
    # ### end Alembic commands ###
