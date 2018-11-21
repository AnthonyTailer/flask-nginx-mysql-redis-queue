"""Add dictalchemy

Revision ID: c5fe5bc8c79c
Revises: 45c4ea852fb0
Create Date: 2018-10-08 22:53:08.418548

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'c5fe5bc8c79c'
down_revision = '45c4ea852fb0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('word_evaluation')
    op.drop_table('patients')
    op.drop_table('words')
    op.drop_table('tasks')
    op.drop_table('users')
    op.drop_table('transcription')
    op.drop_table('evaluations')
    op.drop_table('revoked_tokens')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('revoked_tokens',
    sa.Column('id', mysql.INTEGER(display_width=11), nullable=False),
    sa.Column('jti', mysql.VARCHAR(collation='utf8_bin', length=120), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8_bin',
    mysql_default_charset='utf8',
    mysql_engine='InnoDB'
    )
    op.create_table('evaluations',
    sa.Column('id', mysql.INTEGER(display_width=11), nullable=False),
    sa.Column('date', sa.DATE(), nullable=False),
    sa.Column('type', mysql.VARCHAR(collation='utf8_bin', length=1), nullable=False),
    sa.Column('patient_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.Column('evaluator_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['evaluator_id'], ['users.id'], name='evaluations_ibfk_1'),
    sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], name='evaluations_ibfk_2'),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8_bin',
    mysql_default_charset='utf8',
    mysql_engine='InnoDB'
    )
    op.create_table('transcription',
    sa.Column('id', mysql.INTEGER(display_width=11), nullable=False),
    sa.Column('transcription', mysql.VARCHAR(collation='utf8_bin', length=255), nullable=False),
    sa.Column('type', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.Column('word_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['word_id'], ['words.id'], name='transcription_ibfk_1', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8_bin',
    mysql_default_charset='utf8',
    mysql_engine='InnoDB'
    )
    op.create_table('users',
    sa.Column('id', mysql.INTEGER(display_width=11), nullable=False),
    sa.Column('username', mysql.VARCHAR(collation='utf8_bin', length=120), nullable=False),
    sa.Column('fullname', mysql.VARCHAR(collation='utf8_bin', length=255), nullable=False),
    sa.Column('password', mysql.VARCHAR(collation='utf8_bin', length=120), nullable=False),
    sa.Column('type', mysql.VARCHAR(collation='utf8_bin', length=120), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8_bin',
    mysql_default_charset='utf8',
    mysql_engine='InnoDB'
    )
    op.create_table('tasks',
    sa.Column('id', mysql.VARCHAR(collation='utf8_bin', length=36), nullable=False),
    sa.Column('name', mysql.VARCHAR(collation='utf8_bin', length=128), nullable=True),
    sa.Column('description', mysql.VARCHAR(collation='utf8_bin', length=128), nullable=True),
    sa.Column('user_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.Column('complete', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='tasks_ibfk_1'),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8_bin',
    mysql_default_charset='utf8',
    mysql_engine='InnoDB'
    )
    op.create_table('words',
    sa.Column('id', mysql.INTEGER(display_width=11), nullable=False),
    sa.Column('word', mysql.VARCHAR(collation='utf8_bin', length=255), nullable=False),
    sa.Column('tip', mysql.VARCHAR(collation='utf8_bin', length=255), nullable=True),
    sa.Column('order', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8_bin',
    mysql_default_charset='utf8',
    mysql_engine='InnoDB'
    )
    op.create_table('patients',
    sa.Column('id', mysql.INTEGER(display_width=11), nullable=False),
    sa.Column('name', mysql.VARCHAR(collation='utf8_bin', length=255), nullable=False),
    sa.Column('birth', sa.DATE(), nullable=False),
    sa.Column('sex', mysql.VARCHAR(collation='utf8_bin', length=1), nullable=True),
    sa.Column('school', mysql.VARCHAR(collation='utf8_bin', length=255), nullable=False),
    sa.Column('school_type', mysql.VARCHAR(collation='utf8_bin', length=3), nullable=True),
    sa.Column('caregiver', mysql.VARCHAR(collation='utf8_bin', length=255), nullable=True),
    sa.Column('phone', mysql.VARCHAR(collation='utf8_bin', length=255), nullable=True),
    sa.Column('city', mysql.VARCHAR(collation='utf8_bin', length=255), nullable=False),
    sa.Column('state', mysql.VARCHAR(collation='utf8_bin', length=2), nullable=False),
    sa.Column('address', mysql.VARCHAR(collation='utf8_bin', length=255), nullable=True),
    sa.Column('created_at', sa.DATE(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8_bin',
    mysql_default_charset='utf8',
    mysql_engine='InnoDB'
    )
    op.create_table('word_evaluation',
    sa.Column('evaluation_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.Column('word_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.Column('transcription_target_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.Column('transcription_eval', mysql.VARCHAR(collation='utf8_bin', length=255), nullable=True),
    sa.Column('repetition', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True),
    sa.Column('audio_path', mysql.VARCHAR(collation='utf8_bin', length=255), nullable=False),
    sa.Column('ml_eval', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True),
    sa.Column('api_eval', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True),
    sa.Column('therapist_eval', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['evaluation_id'], ['evaluations.id'], name='word_evaluation_ibfk_1'),
    sa.ForeignKeyConstraint(['transcription_target_id'], ['transcription.id'], name='word_evaluation_ibfk_2'),
    sa.ForeignKeyConstraint(['word_id'], ['words.id'], name='word_evaluation_ibfk_3'),
    sa.PrimaryKeyConstraint('evaluation_id', 'word_id'),
    mysql_collate='utf8_bin',
    mysql_default_charset='utf8',
    mysql_engine='InnoDB'
    )
    # ### end Alembic commands ###