"""empty message

Revision ID: 42aaa123515b
Revises: 625f61bc6fad
Create Date: 2021-01-27 15:51:36.708410

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '42aaa123515b'
down_revision = '625f61bc6fad'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('front_posts', sa.Column('is_delete', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('front_posts', 'is_delete')
    # ### end Alembic commands ###