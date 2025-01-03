# pylint: disable=invalid-name
"""empty message

Revision ID: e8f6ad35d0f0
Revises: fcd59de9d36d
Create Date: 2023-02-06 13:29:55.303906

"""
from alembic import op
import sqlalchemy as sa
from models.alchemy.dashboard import ReportRunStatusEnum

# revision identifiers, used by Alembic.
revision = 'e8f6ad35d0f0'
down_revision = 'fcd59de9d36d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('dashboard_report_run', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'status',
                sa.String(),
                nullable=False,
                server_default=ReportRunStatusEnum.SUCCESS.name,
            )
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('dashboard_report_run', schema=None) as batch_op:
        batch_op.drop_column('status')

    # ### end Alembic commands ###
