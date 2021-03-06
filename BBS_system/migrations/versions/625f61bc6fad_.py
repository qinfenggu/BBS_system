"""empty message

Revision ID: 625f61bc6fad
Revises: 0f4a78595c6c
Create Date: 2021-01-27 14:58:30.000141

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '625f61bc6fad'
down_revision = '0f4a78595c6c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('front_posts',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('title', sa.String(length=100), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('content_html', sa.Text(), nullable=True),
    sa.Column('create_time', sa.DateTime(), nullable=True),
    sa.Column('board_id', sa.Integer(), nullable=True),
    sa.Column('author_id', sa.String(length=100), nullable=True),
    sa.ForeignKeyConstraint(['author_id'], ['front_user.id'], ),
    sa.ForeignKeyConstraint(['board_id'], ['cms_board.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('posts')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('posts',
    sa.Column('id', mysql.INTEGER(display_width=11), autoincrement=True, nullable=False),
    sa.Column('title', mysql.VARCHAR(length=100), nullable=False),
    sa.Column('content', mysql.TEXT(), nullable=False),
    sa.Column('content_html', mysql.TEXT(), nullable=True),
    sa.Column('create_time', mysql.DATETIME(), nullable=True),
    sa.Column('board_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.Column('author_id', mysql.VARCHAR(length=100), nullable=True),
    sa.ForeignKeyConstraint(['author_id'], ['front_user.id'], name='posts_ibfk_1'),
    sa.ForeignKeyConstraint(['board_id'], ['cms_board.id'], name='posts_ibfk_2'),
    sa.PrimaryKeyConstraint('id'),
    mysql_default_charset='utf8',
    mysql_engine='InnoDB'
    )
    op.drop_table('front_posts')
    # ### end Alembic commands ###
