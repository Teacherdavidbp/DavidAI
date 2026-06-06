"""Upgrade trusted_contacts for MVP — full_name, relationship, is_primary, updated_at.

Revision ID: 003_trusted_contacts
Revises: 002_chat_tables
Create Date: 2026-06-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_trusted_contacts"
down_revision: Union[str, None] = "002_chat_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("trusted_contacts", "name", new_column_name="full_name")
    op.alter_column("trusted_contacts", "phone", new_column_name="phone_number")
    op.alter_column("trusted_contacts", "phone_number", nullable=True)

    op.add_column(
        "trusted_contacts",
        sa.Column("relationship", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "trusted_contacts",
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column(
        "trusted_contacts",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.drop_column("trusted_contacts", "notify_sms")
    op.drop_column("trusted_contacts", "notify_email")


def downgrade() -> None:
    op.add_column(
        "trusted_contacts",
        sa.Column("notify_email", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column(
        "trusted_contacts",
        sa.Column("notify_sms", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )

    op.drop_column("trusted_contacts", "updated_at")
    op.drop_column("trusted_contacts", "is_primary")
    op.drop_column("trusted_contacts", "relationship")

    op.alter_column("trusted_contacts", "phone_number", nullable=False)
    op.alter_column("trusted_contacts", "phone_number", new_column_name="phone")
    op.alter_column("trusted_contacts", "full_name", new_column_name="name")
