"""enable unaccent extension

Revision ID: 464203985226
Revises: 58f9feb8f6d9
Create Date: 2026-08-07 18:51:13.337961

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "464203985226"
down_revision: str | None = "58f9feb8f6d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Recherche insensible aux accents (MOD-C03 : "leviator" doit trouver
    # "Léviator") — pas autogénérable par Alembic, extension standard fournie
    # par l'image postgres:16-alpine.
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS unaccent")
