"""Password hash to Text

Revision ID: b8bd1ed4f1bd
Revises: drop_legacy_user_cols
Create Date: 2025-06-09 21:54:03.943465

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b8bd1ed4f1bd'
down_revision = 'drop_legacy_user_cols'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        'users',
        'password_hash',
        type_=sa.Text(),
        existing_type=sa.String(length=128),
        existing_nullable=False
    )


def downgrade():
    op.alter_column(
        'users',
        'password_hash',
        type_=sa.String(length=128),
        existing_type=sa.Text(),
        existing_nullable=False
    )

