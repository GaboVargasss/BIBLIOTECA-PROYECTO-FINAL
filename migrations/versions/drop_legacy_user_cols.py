"""Drop legacy user columns

Revision ID: 4b2e92c341fd_drop_legacy_user_columns
Revises: 2de1c62f0bd2
Create Date: 2025-06-xx xx:xx:xx.xxxxxx
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'drop_legacy_user_cols'
down_revision = '2de1c62f0bd2'
branch_labels = None
depends_on = None

def upgrade():
    # Eliminamos las columnas antiguas que ya no usa tu modelo User
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('first_name')
        batch_op.drop_column('last_name')
        batch_op.drop_column('phone')
        batch_op.drop_column('address')

def downgrade():
    # Para revertir, las volveríamos a crear (opcional)
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('address', sa.String(length=128), nullable=False))
        batch_op.add_column(sa.Column('phone', sa.String(length=20), nullable=False))
        batch_op.add_column(sa.Column('last_name', sa.String(length=64), nullable=False))
        batch_op.add_column(sa.Column('first_name', sa.String(length=64), nullable=False))
