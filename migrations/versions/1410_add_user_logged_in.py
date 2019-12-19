"""Add column users.logged_in

Revision ID: 1410
Revises: 1400
Create Date: 2019-12-19 15:41:33.162634

"""
from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision = '1410'
down_revision = '1400'


def upgrade():
    op.add_column('users', sa.Column('logged_in', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    op.drop_column('users', 'logged_in')

