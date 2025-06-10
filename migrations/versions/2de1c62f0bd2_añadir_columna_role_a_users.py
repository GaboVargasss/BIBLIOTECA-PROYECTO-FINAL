"""Añadir columna role a users

Revision ID: 2de1c62f0bd2
Revises: <hash_anterior>
Create Date: 2025-06-09 18:00:29.729268
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2de1c62f0bd2'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Solo añadimos la columna role a la tabla users
    op.add_column(
        'users',
        sa.Column('role', sa.String(length=10), nullable=False, server_default='user')
    )
    # Quitamos el default para que futuros inserts requieran asignar role explícitamente
    op.alter_column('users', 'role', server_default=None)

def downgrade():
    # En rollback, simplemente eliminamos la columna role
    op.drop_column('users', 'role')
