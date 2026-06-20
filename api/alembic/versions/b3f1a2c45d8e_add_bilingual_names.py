"""add bilingual names to pokemon

Revision ID: b3f1a2c45d8e
Revises: 2b8de7c337ed
Create Date: 2026-06-20
"""

import sqlalchemy as sa
from alembic import op

revision = "b3f1a2c45d8e"
down_revision = "2b8de7c337ed"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("pokemon", "name", new_column_name="name_en")
    op.add_column("pokemon", sa.Column("name_fr", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("pokemon", "name_fr")
    op.alter_column("pokemon", "name_en", new_column_name="name")
