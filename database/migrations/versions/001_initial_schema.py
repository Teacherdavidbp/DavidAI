"""Initial schema — users, trusted_contacts, sos_alerts, subscriptions.

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-06-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "trusted_contacts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("notify_sms", sa.Boolean(), nullable=False),
        sa.Column("notify_email", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trusted_contacts_user_id"), "trusted_contacts", ["user_id"], unique=False)

    op.create_table(
        "sos_alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sos_alerts_user_id"), "sos_alerts", ["user_id"], unique=False)

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plan", sa.String(length=64), nullable=False),
        sa.Column("price_gbp", sa.Float(), nullable=False),
        sa.Column("stripe_customer_id", sa.String(length=255), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_subscriptions_user_id"), "subscriptions", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_subscriptions_user_id"), table_name="subscriptions")
    op.drop_table("subscriptions")
    op.drop_index(op.f("ix_sos_alerts_user_id"), table_name="sos_alerts")
    op.drop_table("sos_alerts")
    op.drop_index(op.f("ix_trusted_contacts_user_id"), table_name="trusted_contacts")
    op.drop_table("trusted_contacts")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
