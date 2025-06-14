"""Initial schema
 
Revision ID: afc76d75f768
Revises: b8bd1ed4f1bd
Create Date: 2025-06-11 18:01:24.348632
"""
from alembic import op
import sqlalchemy as sa
 
# revision identifiers, used by Alembic.
revision = 'afc76d75f768'
down_revision = 'b8bd1ed4f1bd'
branch_labels = None
depends_on = None
 
def upgrade():
    # Crear tabla categories
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=64), nullable=False, unique=True),
    )
 
    # Crear tabla users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('ci', sa.String(length=20), nullable=False, unique=True),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('role', sa.String(length=10), nullable=False)
    )
 
    # Crear tabla books
    op.create_table(
        'books',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('author', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('categories.id'), nullable=True)
    )
 
    # Si necesitas índices o secuencias adicionales, añádelos aquí
    # por ejemplo:
    # op.create_index('ix_books_title', 'books', ['title'])
 
def downgrade():
    # Al revertir, simplemente eliminar las tablas creadas
    op.drop_table('books')
    op.drop_table('users')
    op.drop_table('categories')