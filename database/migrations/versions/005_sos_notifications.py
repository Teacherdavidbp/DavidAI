"""SOS notifications — simulated SMS records for trusted contact alerts.

Revision ID: 005_sos_notifications
Revises: 004_sos_alerts
Create Date: 2026-06-06

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_sos_notifications"
down_revision: Union[str, None] = "004_sos_alerts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sos_notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("sos_alert_id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("channel", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["contact_id"], ["trusted_contacts.id"]),
        sa.ForeignKeyConstraint(["sos_alert_id"], ["sos_alerts.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_sos_notifications_user_id"),
        "sos_notifications",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sos_notifications_sos_alert_id"),
        "sos_notifications",
        ["sos_alert_id"],
        unique=False,
    )
    op.create_check_constraint(
        "ck_sos_notifications_channel",
        "sos_notifications",
        "channel IN ('sms', 'email', 'push')",
    )
    op.create_check_constraint(
        "ck_sos_notifications_status",
        "sos_notifications",
        "status IN ('pending', 'simulated', 'sent', 'failed')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_sos_notifications_status", "sos_notifications", type_="check")
    op.drop_constraint("ck_sos_notifications_channel", "sos_notifications", type_="check")
    op.drop_index(op.f("ix_sos_notifications_sos_alert_id"), table_name="sos_notifications")
    op.drop_index(op.f("ix_sos_notifications_user_id"), table_name="sos_notifications")
    op.drop_table("sos_notifications")
